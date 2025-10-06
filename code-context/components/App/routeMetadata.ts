import { getOCMResourceType, ocmResourceType } from '~/common/analytics';

/**
 * match pathname to analytics metadata
 * https://docs.google.com/spreadsheets/d/1C_WJWPy3sgE2ICaYHgWpWngj0A3Z3zl5GcstWySG9WE/edit#gid=0
 */
export const metadataByRoute = (
  pathname: string,
  planType: string,
  clusterId: string,
  externalClusterId?: string,
): {
  ['ocm_cluster_id']?: string;
  ['ocm_resource_type']: string | undefined;
  title?: string;
  path?: string;
  ['resource_id']?: string;
} => {
  /**
   * Note: Order matters here
   * Statements are sorted by the matcher clause, from more specific to less specific
   * i.e. check for "osdtrial" must precede "osd"
   */

  const clusterDetails = {
    ocm_cluster_id: clusterId,
    ...(externalClusterId ? { resource_id: externalClusterId } : {}),
  };

  if (pathname.startsWith('/archived')) {
    return { ocm_resource_type: ocmResourceType.ALL };
  }
  if (pathname.startsWith('/assisted-installer')) {
    return { ocm_resource_type: ocmResourceType.OCP_AssistedInstall };
  }
  if (pathname.startsWith('/create/osdtrial')) {
    return { ocm_resource_type: ocmResourceType.OSDTrial };
  }
  if (pathname.startsWith('/create/osd')) {
    return { ocm_resource_type: ocmResourceType.OSD };
  }
  if (pathname.startsWith('/create/rosa')) {
    return { ocm_resource_type: ocmResourceType.MOA };
  }
  if (pathname.startsWith('/create')) {
    return { ocm_resource_type: ocmResourceType.ALL };
  }
  if (pathname.match(/\/details\/s\/.*\/add-idp/)) {
    return {
      ocm_resource_type: getOCMResourceType(planType),
      title: 'Add IdP',
      path: '/openshift/details/s/add-idp',
      ...clusterDetails,
    };
  }
  if (pathname.match(/\/details\/s\/.*\/edit-idp/)) {
    return {
      ocm_resource_type: getOCMResourceType(planType),
      title: 'Edit IdP',
      path: '/openshift/details/s/edit-idp',
      ...clusterDetails,
    };
  }
  if (pathname.startsWith('/details/s/')) {
    // TODO: There's a bug that sends this with planType UNKNOWN
    return {
      ocm_resource_type: getOCMResourceType(planType),
      title: 'View Cluster',
      path: '/openshift/details/s',
      ...clusterDetails,
    };
  }
  if (pathname.startsWith('/install/azure/aro-provisioned')) {
    return { ocm_resource_type: ocmResourceType.ARO };
  }
  if (pathname.startsWith('/install/pull-secret')) {
    return { ocm_resource_type: ocmResourceType.ALL };
  }
  if (pathname.startsWith('/install')) {
    return { ocm_resource_type: ocmResourceType.OCP };
  }
  if (pathname.startsWith('/dashboard')) {
    return { ocm_resource_type: ocmResourceType.ALL };
  }
  if (pathname.startsWith('/quota')) {
    return { ocm_resource_type: ocmResourceType.ALL };
  }
  if (pathname.startsWith('/register')) {
    return { ocm_resource_type: ocmResourceType.OCP };
  }
  if (pathname.startsWith('/releases')) {
    return { ocm_resource_type: ocmResourceType.OCP };
  }
  if (pathname.startsWith('/token/rosa')) {
    return { ocm_resource_type: ocmResourceType.MOA };
  }
  if (pathname.startsWith('/token')) {
    return { ocm_resource_type: ocmResourceType.ALL };
  }

  return { ocm_resource_type: ocmResourceType.ALL };
};

// TODO: Better way to determine this?
export const is404 = () => {
  const el = document.querySelector('#not-found h1');
  if (el instanceof HTMLElement && el.innerText === 'We lost that page') {
    return true;
  }
  return false;
};
