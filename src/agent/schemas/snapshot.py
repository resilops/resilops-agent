from typing import List

from pydantic import UUID4, BaseModel, Field
from reslib.k8s.schema import NamespaceState


class ClusterSnapshot(BaseModel):
    """
    Request model representing a snapshot of a Kubernetes cluster state.

    This model is used to capture the state of the cluster at a specific
    synchronization point. It includes a unique identifier for the snapshot
    operation and a collection of namespace states observed during that sync..
    """

    sync_uuid: UUID4 = Field(..., description="UUID of the snapshot sync")
    namespaces: List[NamespaceState] = Field(
        ..., description="List of namespace states"
    )
