from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from kubernetes.client import V1Lease, V1LeaseSpec
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException

from agent.core.leader import KubernetesLeaderElection


def build_election(identity="agent-1", lease_duration_seconds=30):
    with patch.object(
        KubernetesLeaderElection, "_build_api_client", return_value=Mock()
    ):
        return KubernetesLeaderElection(
            lease_name="agent-lease",
            namespace="resilops",
            identity=identity,
            lease_duration_seconds=lease_duration_seconds,
        )


def test_build_identity_uses_hostname_and_pid():
    with (
        patch("agent.core.leader.socket.gethostname", return_value="host-a"),
        patch("agent.core.leader.os.getpid", return_value=1234),
    ):
        assert KubernetesLeaderElection._build_identity() == "host-a-1234"


def test_build_api_client_prefers_incluster_and_falls_back_to_kubeconfig():
    with (
        patch("agent.core.leader.client.CoordinationV1Api", return_value="api"),
        patch("agent.core.leader.config.load_incluster_config") as incluster,
        patch("agent.core.leader.config.load_kube_config") as kubeconfig,
    ):
        assert KubernetesLeaderElection._build_api_client() == "api"

    incluster.assert_called_once()
    kubeconfig.assert_not_called()

    with (
        patch("agent.core.leader.client.CoordinationV1Api", return_value="api"),
        patch(
            "agent.core.leader.config.load_incluster_config",
            side_effect=ConfigException("no in-cluster"),
        ) as incluster,
        patch("agent.core.leader.config.load_kube_config") as kubeconfig,
    ):
        assert KubernetesLeaderElection._build_api_client() == "api"

    incluster.assert_called_once()
    kubeconfig.assert_called_once()


def test_set_leader_and_is_leader_property():
    election = build_election()

    assert election.is_leader is False
    election._set_leader(True)
    assert election.is_leader is True


def test_now_returns_timezone_aware_utc_datetime():
    now = KubernetesLeaderElection._now()

    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc


def test_read_lease_uses_namespaced_lease_api():
    election = build_election()
    lease = object()
    election.api.read_namespaced_lease.return_value = lease

    assert election._read_lease() is lease
    election.api.read_namespaced_lease.assert_called_once_with(
        name="agent-lease", namespace="resilops"
    )


def test_build_new_lease_uses_identity_and_duration():
    election = build_election(identity="agent-42", lease_duration_seconds=45)
    fixed_now = datetime(2026, 7, 4, tzinfo=timezone.utc)

    with patch.object(election, "_now", return_value=fixed_now):
        lease = election._build_new_lease()

    assert lease.metadata.name == "agent-lease"
    assert lease.metadata.namespace == "resilops"
    assert lease.spec.holder_identity == "agent-42"
    assert lease.spec.acquire_time == fixed_now
    assert lease.spec.renew_time == fixed_now
    assert lease.spec.lease_duration_seconds == 45


def test_try_create_lease_sets_leadership_on_success_and_conflict():
    election = build_election()

    with patch.object(election, "_build_new_lease", return_value="lease-body"):
        assert election._try_create_lease() is True

    election.api.create_namespaced_lease.assert_called_once_with(
        namespace="resilops", body="lease-body"
    )
    assert election.is_leader is True

    election = build_election()
    election.api.create_namespaced_lease.side_effect = ApiException(status=409)

    with patch.object(election, "_build_new_lease", return_value="lease-body"):
        assert election._try_create_lease() is False

    assert election.is_leader is False


def test_try_create_lease_reraises_unexpected_api_errors():
    election = build_election()
    election.api.create_namespaced_lease.side_effect = ApiException(status=500)

    with patch.object(election, "_build_new_lease", return_value="lease-body"):
        with pytest.raises(ApiException):
            election._try_create_lease()


def test_can_acquire_or_renew_for_current_holder_or_expired_lease():
    election = build_election(identity="agent-1")
    now = datetime(2026, 7, 4, tzinfo=timezone.utc)

    assert election._can_acquire_or_renew(
        V1LeaseSpec(holder_identity="agent-1"), now=now
    )

    with patch.object(election, "_is_lease_expired", return_value=True) as expired:
        assert election._can_acquire_or_renew(
            V1LeaseSpec(holder_identity="other"), now=now
        )

    expired.assert_called_once()


def test_is_lease_expired_handles_missing_and_elapsed_renew_time():
    election = build_election(lease_duration_seconds=30)
    now = datetime(2026, 7, 4, 12, 0, tzinfo=timezone.utc)

    assert election._is_lease_expired(V1LeaseSpec(renew_time=None), now=now) is True
    assert (
        election._is_lease_expired(
            V1LeaseSpec(
                renew_time=now - timedelta(seconds=31),
                lease_duration_seconds=30,
            ),
            now=now,
        )
        is True
    )
    assert (
        election._is_lease_expired(
            V1LeaseSpec(
                renew_time=now - timedelta(seconds=10),
                lease_duration_seconds=30,
            ),
            now=now,
        )
        is False
    )


def test_build_updated_lease_preserves_acquire_time_and_updates_holder():
    election = build_election(identity="agent-2", lease_duration_seconds=60)
    now = datetime(2026, 7, 4, 12, 0, tzinfo=timezone.utc)
    original_acquire_time = now - timedelta(minutes=1)
    lease = V1Lease(spec=V1LeaseSpec(holder_identity="other"))
    spec = V1LeaseSpec(
        holder_identity="other",
        acquire_time=original_acquire_time,
        renew_time=now - timedelta(seconds=20),
        lease_duration_seconds=15,
    )

    updated = election._build_updated_lease(lease=lease, spec=spec, now=now)

    assert updated is lease
    assert updated.spec.holder_identity == "agent-2"
    assert updated.spec.acquire_time == original_acquire_time
    assert updated.spec.renew_time == now
    assert updated.spec.lease_duration_seconds == 60


def test_replace_lease_sets_leadership_and_handles_conflict():
    election = build_election()
    lease = V1Lease()

    assert election._replace_lease(lease) is True
    election.api.replace_namespaced_lease.assert_called_once_with(
        name="agent-lease", namespace="resilops", body=lease
    )
    assert election.is_leader is True

    election = build_election()
    election.api.replace_namespaced_lease.side_effect = ApiException(status=409)
    assert election._replace_lease(lease) is False
    assert election.is_leader is False


def test_replace_lease_reraises_unexpected_api_errors():
    election = build_election()
    election.api.replace_namespaced_lease.side_effect = ApiException(status=500)

    with pytest.raises(ApiException):
        election._replace_lease(V1Lease())


def test_try_take_or_renew_existing_lease_returns_false_when_not_allowed():
    election = build_election()
    lease = V1Lease(spec=V1LeaseSpec())
    now = datetime(2026, 7, 4, tzinfo=timezone.utc)

    with patch.object(election, "_can_acquire_or_renew", return_value=False):
        assert election._try_take_or_renew_existing_lease(lease=lease, now=now) is False

    assert election.is_leader is False


def test_try_take_or_renew_existing_lease_builds_and_replaces_when_allowed():
    election = build_election()
    lease = V1Lease(spec=V1LeaseSpec())
    now = datetime(2026, 7, 4, tzinfo=timezone.utc)

    with (
        patch.object(election, "_can_acquire_or_renew", return_value=True),
        patch.object(election, "_build_updated_lease", return_value="updated"),
        patch.object(election, "_replace_lease", return_value=True) as replace,
    ):
        assert election._try_take_or_renew_existing_lease(lease=lease, now=now) is True

    replace.assert_called_once_with("updated")


def test_acquire_or_renew_lease_reads_then_renews_or_creates_on_404():
    election = build_election()
    lease = V1Lease(spec=V1LeaseSpec())
    now = datetime(2026, 7, 4, tzinfo=timezone.utc)

    with (
        patch.object(election, "_now", return_value=now),
        patch.object(election, "_read_lease", return_value=lease) as read_lease,
        patch.object(
            election, "_try_take_or_renew_existing_lease", return_value=True
        ) as renew,
    ):
        assert election.acquire_or_renew_lease() is True

    read_lease.assert_called_once()
    renew.assert_called_once_with(lease=lease, now=now)

    election = build_election()
    with (
        patch.object(election, "_now", return_value=now),
        patch.object(election, "_read_lease", side_effect=ApiException(status=404)),
        patch.object(election, "_try_create_lease", return_value=True) as create,
    ):
        assert election.acquire_or_renew_lease() is True

    create.assert_called_once()


def test_acquire_or_renew_lease_reraises_non_404_read_errors():
    election = build_election()

    with patch.object(election, "_read_lease", side_effect=ApiException(status=500)):
        with pytest.raises(ApiException):
            election.acquire_or_renew_lease()
