import axios, { AxiosInstance, AxiosResponse } from 'axios';

import { hasOwnErrorPage } from '../../../common/errors';

const apiErrorInterceptor = (
  apiRequest: AxiosInstance,
  showApiError: (error: AxiosResponse) => void,
) => {
  const interceptorID = apiRequest.interceptors.response.use(
    (response) => response,
    (error) => {
      // watch only errors that have their own error pages
      if (axios.isAxiosError(error) && error.response && hasOwnErrorPage(error.response)) {
        // show the error page and handle error there
        showApiError(error.response);
      }
      return Promise.reject(error);
    },
  );
  // return the handle to eject this interceptor
  return () => {
    apiRequest.interceptors.response.eject(interceptorID);
  };
};

export default apiErrorInterceptor;
