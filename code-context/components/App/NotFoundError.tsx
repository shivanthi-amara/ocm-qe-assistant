import React from 'react';

import { MissingPage } from '@patternfly/react-component-groups';
import { EmptyState, EmptyStateBody } from '@patternfly/react-core';

import { AppPage } from './AppPage';

import './NotFoundError.scss';

const NotFoundError = () => (
  <AppPage>
    <EmptyState id="not-found" data-testid="not-found">
      <EmptyStateBody>
        <MissingPage />
      </EmptyStateBody>
    </EmptyState>
  </AppPage>
);

export default NotFoundError;
