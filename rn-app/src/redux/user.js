export default(state = {
	customerDetails: null,
	customerAccessToken: null,
	forgotPasswordStatus: null,
	isUserFirstTime: true,
	rememberMeData:undefined
}, action) => {
	switch(action.type){
		case 'RESET_USER_STATE':
			state = {
				...state,
				customerDetails: null,
				customerAccessToken: null,
				forgotPasswordStatus: null
			}

      break;

		case 'STORE_ACCESS_TOKEN':
			state = {
				...state,
				customerAccessToken: action.payload
			}

      break;

		case 'SET_FORGOT_PASSWORD_STATUS':
			state = {
				...state,
				forgotPasswordStatus: action.payload
			}

			break;

		case 'LOADED_CUSTOMER_DETAILS':
			state = {
				...state,
				customerDetails: action.payload
			}

			break;

		case 'UPDATED_CUSTOMER_DETAILS':
			state = {
				...state,
				updatingCustomerDetails: false,
				customerDetails: {
					...state.customerDetails,
					...action.payload
				}
			}

			break;

		case 'UPDATING_CUSTOMER_DETAILS':
			state = {
				...state,
				updatingCustomerDetails: true
			}
			break;
		case 'UPDATING_CUSTOMER_DETAILS_ERROR':
			state = {
				...state,
				updatingCustomerDetails: false
			}

			break;
		case 'IS_USER_FIRST_TIME':
			state = {
				...state,
				isUserFirstTime: false
			}

			break;
		case 'REMEMBER_ME':
			state = {
				...state,
				rememberMeData: action.payload
			}

			break;

    default:
      break;
  }

  return state;
}