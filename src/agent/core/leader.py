import os
import socket
from datetime import datetime, timedelta, timezone
from typing import Optional

from kubernetes import client, config
from kubernetes.client import V1Lease, V1LeaseSpec, V1ObjectMeta
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException


class KubernetesLeaderElection:
    """Lease-based Kubernetes leader election."""

    def __init__(
        self,
        lease_name: str,
        namespace: str,
        identity: Optional[str] = None,
        lease_duration_seconds: int = 30,
    ) -> None:
        """
        Initialize leader election state and Kubernetes coordination client.

        Args:
            lease_name: Name of the Lease resource.
            namespace: Namespace containing the Lease resource.
            identity: Unique identity for this instance. If omitted, a hostname/pid
                based identity is generated.
            lease_duration_seconds: Duration for which the lease is valid.
        """
        self.lease_name = lease_name
        self.namespace = namespace
        self.identity = identity or self._build_identity()
        self.lease_duration_seconds = lease_duration_seconds

        self._is_leader = False

        self.api = self._build_api_client()

    @property
    def is_leader(self) -> bool:
        """Return whether this instance currently believes it is leader."""
        return self._is_leader

    def acquire_or_renew_lease(self) -> bool:
        """
        Acquire the lease or renew it if already owned.

        Returns:
            True if this instance is leader after the operation, otherwise False.

        Raises:
            ApiException: If Kubernetes returns an unexpected API error.
        """
        now = self._now()
        try:
            lease = self._read_lease()
        except ApiException as exc:
            if exc.status == 404:
                return self._try_create_lease()
            raise

        return self._try_take_or_renew_existing_lease(lease=lease, now=now)

    @staticmethod
    def _build_api_client() -> client.CoordinationV1Api:
        """
        Initialize in-cluster Kubernetes configuration and coordination client.

        Returns:
            Configured CoordinationV1Api instance.
        """
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config()
        return client.CoordinationV1Api()

    @staticmethod
    def _build_identity() -> str:
        """
        Build a unique holder identity for this process.

        Returns:
            Identity string derived from hostname and process id.
        """
        return f"{socket.gethostname()}-{os.getpid()}"

    def _set_leader(self, value: bool) -> None:
        """
        Update the cached leadership flag.

        Args:
            value: New leadership state.
        """
        self._is_leader = value

    @staticmethod
    def _now() -> datetime:
        """
        Return the current UTC time.

        Returns:
            Timezone-aware UTC datetime.
        """
        return datetime.now(timezone.utc)

    def _read_lease(self) -> V1Lease:
        """
        Read the current Lease from Kubernetes.

        Returns:
            Existing Lease object.

        Raises:
            ApiException: If the lease cannot be read.
        """
        return self.api.read_namespaced_lease(
            name=self.lease_name,
            namespace=self.namespace,
        )

    def _build_new_lease(self) -> V1Lease:
        """
        Build a new Lease resource body for initial acquisition.

        Returns:
            Lease object owned by this instance.
        """
        now = self._now()
        return V1Lease(
            metadata=V1ObjectMeta(
                name=self.lease_name,
                namespace=self.namespace,
            ),
            spec=V1LeaseSpec(
                holder_identity=self.identity,
                acquire_time=now,
                renew_time=now,
                lease_duration_seconds=self.lease_duration_seconds,
            ),
        )

    def _try_create_lease(self) -> bool:
        """
        Try to create the Lease when it does not yet exist.

        Returns:
            True if creation succeeded and leadership was acquired, otherwise False.

        Raises:
            ApiException: If Kubernetes returns an unexpected API error.
        """
        try:
            self.api.create_namespaced_lease(
                namespace=self.namespace,
                body=self._build_new_lease(),
            )
            self._set_leader(True)
            return True
        except ApiException as exc:
            if exc.status == 409:
                self._set_leader(False)
                return False
            raise

    def _try_take_or_renew_existing_lease(self, lease: V1Lease, now: datetime) -> bool:
        """
        Try to take over an expired lease or renew a lease already owned
        by this instance.

        Args:
            lease: Existing lease resource.
            now: Current UTC timestamp.

        Returns:
            True if leadership was acquired or renewed, otherwise False.

        Raises:
            ApiException: If Kubernetes returns an unexpected API error.
        """
        spec = lease.spec or V1LeaseSpec()

        if not self._can_acquire_or_renew(spec=spec, now=now):
            self._set_leader(False)
            return False

        updated_lease = self._build_updated_lease(lease=lease, spec=spec, now=now)
        return self._replace_lease(updated_lease)

    def _can_acquire_or_renew(self, spec: V1LeaseSpec, now: datetime) -> bool:
        """
        Determine whether this instance is allowed to acquire or renew the lease.

        The lease can be updated when:
        - this instance already owns it, or
        - the existing lease is expired

        Args:
            spec: Current lease spec.
            now: Current UTC timestamp.

        Returns:
            True if the lease can be acquired or renewed, otherwise False.
        """
        if spec.holder_identity == self.identity:
            return True

        return self._is_lease_expired(spec=spec, now=now)

    def _is_lease_expired(self, spec: V1LeaseSpec, now: datetime) -> bool:
        """
        Determine whether the current lease is expired.

        Args:
            spec: Current lease spec.
            now: Current UTC timestamp.

        Returns:
            True if the lease is expired or missing renew_time, otherwise False.
        """
        if spec.renew_time is None:
            return True

        lease_duration = spec.lease_duration_seconds or self.lease_duration_seconds
        return spec.renew_time + timedelta(seconds=lease_duration) < now  # noqa

    def _build_updated_lease(
        self,
        lease: V1Lease,
        spec: V1LeaseSpec,
        now: datetime,
    ) -> V1Lease:
        """
        Build an updated lease body for renew or takeover.

        Args:
            lease: Existing lease resource.
            spec: Existing lease spec.
            now: Current UTC timestamp.

        Returns:
            Updated lease resource with this instance as holder.
        """
        lease.spec = V1LeaseSpec(
            holder_identity=self.identity,
            acquire_time=spec.acquire_time or now,
            renew_time=now,
            lease_duration_seconds=self.lease_duration_seconds,
        )
        return lease

    def _replace_lease(self, lease: V1Lease) -> bool:
        """
        Replace the existing Lease resource in Kubernetes.

        Args:
            lease: Updated lease object.

        Returns:
            True if replace succeeded and leadership was obtained, otherwise False.

        Raises:
            ApiException: If Kubernetes returns an unexpected API error.
        """
        try:
            self.api.replace_namespaced_lease(
                name=self.lease_name, namespace=self.namespace, body=lease
            )
            self._set_leader(True)
            return True
        except ApiException as exc:
            if exc.status == 409:
                self._set_leader(False)
                return False
            raise
