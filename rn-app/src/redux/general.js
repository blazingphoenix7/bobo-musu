export default(state = {
	sidemenuRoutes: [],
	homeSlides: [],
	deviceToken: null
}, action) => {
	switch(action.type){
		case 'LOADED_SIDEBAR_MENU_ROUTES':
			state = {
				...state,
				sidemenuRoutes: action.payload
			}

			break;

		case 'LOADED_HOME_SLIDERS':
			state = {
				...state,
				homeSlides: action.payload
			}

			break;

		case 'STORE_NOTIFICATIONS_TOKEN':
			state = {
				...state,
				deviceToken: action.payload
			}

			break;

		default:
			break;
	}

	return state;
}