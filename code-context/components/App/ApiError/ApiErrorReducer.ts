import { AxiosResponse } from 'axios';

import { ApiErrorAction, CLEAR_API_ERROR, SHOW_API_ERROR } from './ApiErrorActions';

type State = AxiosResponse | null;

const initialState: State = null;

// eslint-disable-next-line default-param-last
const apiErrorReducer = (state = initialState, action: ApiErrorAction): State => {
  switch (action.type) {
    case SHOW_API_ERROR:
      return action.payload;
    case CLEAR_API_ERROR:
      return initialState;
    default:
      return state;
  }
};

export default apiErrorReducer;
