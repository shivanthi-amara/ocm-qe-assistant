import { AxiosResponse } from 'axios';
import { action, ActionType } from 'typesafe-actions';

const SHOW_API_ERROR = 'SHOW_API_ERROR';
const CLEAR_API_ERROR = 'CLEAR_API_ERROR';

const apiErrorConstants = {
  SHOW_API_ERROR,
  CLEAR_API_ERROR,
};

const showApiError = (error: AxiosResponse) => action(SHOW_API_ERROR, error);

const clearApiError = () => action(CLEAR_API_ERROR);

const apiErrorActions = { showApiError, clearApiError };

type ApiErrorAction = ActionType<typeof apiErrorActions>;

export {
  apiErrorConstants,
  SHOW_API_ERROR,
  CLEAR_API_ERROR,
  apiErrorActions,
  showApiError,
  clearApiError,
  ApiErrorAction,
};
