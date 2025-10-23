import { NodePool, NodePoolUpgradePolicy } from '~/types/clusters_mgmt.v1';

export interface NodePoolWithUpgradePolicies extends NodePool {
  upgradePolicies?: {
    kind?: 'NodePoolUpgradePolicyList';
    page?: number;
    size?: number;
    total?: number;
    items: NodePoolUpgradePolicy[];
    errorMessage?: string;
  };
}
