import React from 'react';

import { Alert } from '@patternfly/react-core';

export interface WarningProps {
  hasClusterAutoScaler: boolean;
  hasAutoscalingMachinePools: boolean;
  isEnabledOnCurrentPool: boolean;
  warningType: 'editMachinePool' | 'addMachinePool' | 'clusterView';
}

/*
 * It is currently not possible for the UI to correctly identify when a cluster has autoscaler disabled.
 *
 * In particular, for clusters created before the implementation of Cluster Autoscaler that had MP autoscaling enabled,
 * the backend would assign them an autoscaler in Hive. But this autoscaler is not returned via the API.
 *
 * Therefore, we can only show the warnings that are 100% accurate,
 * e.g. when the Cluster has a "new" autoscaler, and the MPs all have autoscaling disabled.
 */
const MachinePoolsAutoScalingWarning = ({
  hasClusterAutoScaler,
  hasAutoscalingMachinePools,
  isEnabledOnCurrentPool,
  warningType,
}: WarningProps) => {
  let message: React.ReactNode | string = '';
  let title = '';
  switch (warningType) {
    case 'clusterView':
      if (hasClusterAutoScaler && !hasAutoscalingMachinePools) {
        title = 'Cluster will not autoscale';
        message =
          'The cluster autoscaling settings will not have any effect as no machine pools are set to autoscale.';
      }
      break;
    case 'addMachinePool':
    case 'editMachinePool':
      if (hasClusterAutoScaler && !isEnabledOnCurrentPool && !hasAutoscalingMachinePools) {
        title = 'Cluster will not autoscale';
        message =
          'Without machine pools which are configured to autoscale, the cluster autoscaler settings will not have any effect on the cluster.';
      }
      break;
    default:
      break;
  }
  return message ? (
    <Alert data-testid="inconsistent-autoscaling-settings" variant="warning" isInline title={title}>
      {message}
    </Alert>
  ) : null;
};

export default MachinePoolsAutoScalingWarning;
