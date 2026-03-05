export default(state = {
	collections: [],
	products: [],
	activeProduct: null,
	selectedProductAttributes: {},
	favoritedProducts: [],
	productFilterData: [],
	productVariants:{},
	assignPrint:undefined,
	productDetails : undefined,
}, action) => {
	switch(action.type){
    case 'RESET_PRODUCTS_STATE':
      state = {
				...state,
				activeProduct: null,
				selectedProductAttributes: {},
				favoritedProducts: []
			}

      break;

		case 'LOADED_COLLECTIONS':
			state = {
				...state,
				collections: action.payload
			}

			break;

		case 'PRODUCTS_FETCH_START':
			state = {
				...state,
				productLoading: true
			}

			break;

		case 'LOADED_PRODUCTS':
			state = {
				...state,
				productLoading: false,
				products: action.payload
			}

			break;
		
		case 'PRODUCTS_FETCH_FINISH':
			state = {
				...state,
				productLoading: false
			}
	
			break;

		case 'LOADED_FAVORITED_PRODUCTS': {
			state = {
				...state,
				favoritedProducts: action.payload 
      		}
			break;
		}

		case 'ADDED_FOVORITED_PRODUCT': {
			state = {
				...state,
				favoritedProducts: [...state.favoritedProducts, action.payload] 
			}

			break;
		}

		case 'REMOVED_FOVORITED_PRODUCT': {
			const favoritedProducts = state.favoritedProducts.filter(product => product.graphql_product_id !== action.payload);

			state = {
				...state,
				favoritedProducts
			}

			break;
		}

		case 'SET_ACTIVE_PRODUCT': {
			state = {
				...state,
				selectedProductAttributes: {},
				activeProduct: action.payload
			}

			break;
		}

		case 'SELECT_PRODUCT_ATTRIBUTES': {
			const {property, value} = action.payload;

			state = {
				...state,
				selectedProductAttributes: {
					...state.selectedProductAttributes,
					[property]: value
				},
			}

			break;
		}
		case 'SET_PRODUCT_FILTER_DATA': {
			state = {
				...state,
				productFilterData: action.payload,
			}
			break;
		}
		case 'SET_PRODUCT_VARIANTS': {
			state = {
				...state,
				productVariants: action.payload,
			}
			break;
		}
		case 'SET_PRODUCT_ASSIGN_PRINT': {
			state = {
				...state,
				assignPrint: action.payload,
			}
			break;
		}
		case 'SET_PRODUCT_DETAILS': {
			state = {
				...state,
				productDetails: action.payload,
			}
			break;
		}

		default:
			break;
	}

	return state;
}