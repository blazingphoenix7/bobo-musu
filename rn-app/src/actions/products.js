import axios from 'axios';
import AsyncStorage from '@react-native-community/async-storage';

import {apiUrl} from '../constants';
import {graphqlApiUrl, storefrontAccessToken, graphqlAdminApiUrl, adminAccessToken} from '../constants';

export const loadCollections = (callback) => {
	return dispatch => {
		axios({
      url: graphqlAdminApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Access-Token': adminAccessToken
      },
      data: {
        query: `
          query {
            collections(first: 20) {
							edges{
								node{
									id,
									handle,
									title,
									description,
									productsCount,
									image {
										originalSrc
									}
								}
							}
            }
          }
        `
      }
		})
		.then(result => {
			const items = result.data?.data?.collections?.edges;
			
			callback && callback(result)
			console.log('collections result-->', JSON.stringify(items));
			if(items){
				const collections = items.map(item => item.node);
				dispatch({
					type: 'LOADED_COLLECTIONS',
					payload: collections
				});
			}
		})
		.catch(console.log);
  };
}

export const loadProducts = (filters = '') => {
	return dispatch => {
		let filtersQuery = '';

		if(Object.keys(filters).length){
			filtersQuery = 'query: "';

			Object.keys(filters).forEach(function(key, i) {
				
				filtersQuery += `${key}:${filters[key]}`;
				if(Object.keys(filters).length - 1 != i ){
					filtersQuery += " AND "
				}
				
			})

			// for(let filter in filters){
			// 	filtersQuery += `${filter}:'${filters[filter]}' `;
			// }

			filtersQuery += '"';
		}
		console.log('filtersQuery-->',filtersQuery);
		dispatch({
			type: 'PRODUCTS_FETCH_START',
		});
		
		axios({
      url: graphqlApiUrl,
      method: 'post',
      headers: {
        'X-Shopify-Storefront-Access-Token': storefrontAccessToken
      },
      data: {
        query: `
          query {
            products(first: 20${filtersQuery}) {
							edges{
								node{
									id,
									handle,
									title,
									description,
									tags,
									availableForSale,
									variants(first: 100) {
										edges {
											node {
												id
												price
												title
												availableForSale
												selectedOptions {
													name
													value
												}
											}
										}
									},
									priceRange {
										minVariantPrice {
											amount,
											currencyCode
										},
										maxVariantPrice {
											amount,
											currencyCode
										}
									},
									images(first: 20) {
										edges {
											node {
												originalSrc
											}
										}
									}
								}
							}
            }
          }
        `
      }
		})
		.then(result => {
			const items = result.data?.data?.products?.edges;
			console.log('product result-->',JSON.stringify(result));
			// console.log(result.data.errors)

			if(items){
				const products = items.map(item => {
					const product = item.node;
					const images = item.node?.images?.edges;
					const variants = item.node?.variants?.edges;

					if(images){
						product.images = images.map(image => image.node.originalSrc)
					}

					if(variants){
						product.variants = variants.map(variant => variant.node)
					}

					return product;
				});
				dispatch({
					type: 'LOADED_PRODUCTS',
					payload: products
				});
			}
		})
		.catch(() =>{
			dispatch({
				type: 'PRODUCTS_FETCH_FINISH',
			});
		});
  };
}

export const setActiveProduct = product => {
	return dispatch => {
		dispatch({
			type: 'SET_ACTIVE_PRODUCT',
			payload: product
		});
	};
}

export const selectProductAttributes = (property, value) => {
	return dispatch => {
		dispatch({
			type: 'SELECT_PRODUCT_ATTRIBUTES',
			payload: {
				property,
				value
			}
		});
	};
}

export const loadFavoritedProducts = customerId => {
	return async dispatch => {
	const customerAccessToken = await AsyncStorage.getItem('accessToken');
	
	console.log('customerAccessToken-->',customerAccessToken);
	console.log('loadFavoritedProducts url-->',`${apiUrl}/shopify/wishlist/${customerId}/`);
	axios.get(`${apiUrl}/shopify/wishlist/${customerId}/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
			}
		})
    .then(res => {
      if (res.status === 200) {
		let wishlistGraphQlIds = res.data?.graphql_product_ids || []
		if(wishlistGraphQlIds.length > 0){
			axios({
				url: graphqlApiUrl,
				method: 'post',
				headers: {
				  'X-Shopify-Storefront-Access-Token': storefrontAccessToken
				},
				data: {
					query: `
						query {
							nodes(ids: ${JSON.stringify(wishlistGraphQlIds)}) {
								...on Product {
									id,
									handle,
									title,
									description,
									tags,
									availableForSale,
									variants(first: 100) {
										edges {
											node {
												id
												price
												title
												availableForSale
												selectedOptions {
													name
													value
												}
											}
										}
									},
									priceRange {
										minVariantPrice {
											amount,
											currencyCode
										},
										maxVariantPrice {
											amount,
											currencyCode
										}
									},
									images(first: 20) {
										edges {
											node {
												originalSrc
											}
										}
									}
								}
							}
						}
					`
				}
				  })
				  .then(result => {
					  const items = result.data?.data?.nodes;
					//   console.log('wishlist product result-->',JSON.stringify(items));
					  // console.log(result.data.errors)
					  let finalFavData = res.data?.results.map((item) =>{
						let productDetail = items.find(x => x.id == item.graphql_product_id);
				
						// const products = items.map(item => {
						// 	const product = item.node;
						// 	const images = item.node?.images?.edges;
						// 	const variants = item.node?.variants?.edges;
		
						// 	if(images){
						// 		product.images = images.map(image => image.node.originalSrc)
						// 	}
		
						// 	if(variants){
						// 		product.variants = variants.map(variant => variant.node)
						// 	}
		
						// 	return product;
						// });
						const images = productDetail.images?.edges;
						const variants = productDetail.variants?.edges;
	
						if(images){
							productDetail.images = images.map(image => image.node.originalSrc)
						}
	
						if(variants){
							productDetail.variants = variants.map(variant => variant.node)
						}
						return {
							...item,
							...productDetail
						}
					  })
					  console.log('finalFavData-->', JSON.stringify(finalFavData));
					  if(finalFavData){
						dispatch({
							type: 'LOADED_FAVORITED_PRODUCTS',
							payload: [...finalFavData]
						  });
					  }
				  })
				  .catch(() =>{
					  dispatch({
						  type: 'PRODUCTS_FETCH_FINISH',
					  });
				  });	
		}
      }
    })
    .catch(err => console.log('ERROR', err));
	};
}

export const addToFavoritedProducts = (customerId, productId) => {
	console.log('customerId, productId-->',customerId, productId);
	return async dispatch => {
		const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.post(`${apiUrl}/shopify/wishlist/`, {
				graphql_customer_id: customerId,
				graphql_product_id: productId
			}, {
		headers: {
			'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
				}
			})
		.then(res => {
		if (res.status === 201) {
			// dispatch({
			// 	type: 'ADDED_FOVORITED_PRODUCT',
			// 	payload: res.data
			// });
			}
		})
		.catch(err => console.log('ERROR', err));
	};
}

export const removeFromFavoritedProducts = (customerId, productId) => {
	return async dispatch => {
    const customerAccessToken = await AsyncStorage.getItem('accessToken');

		axios.delete(`${apiUrl}/shopify/wishlist/${customerId}/${productId}/`, {
      headers: {
        'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken
			}
		})
    .then(res => {
      if (res.status === 200 || res.status === 204) {
        dispatch({
          type: 'REMOVED_FOVORITED_PRODUCT',
          payload: productId
        });
      }
    })
    .catch(err => console.log('ERROR', err));
	};
}

export const loadFilterData = () => {
	return async dispatch => {
		const customerAccessToken = await AsyncStorage.getItem('accessToken');
		axios.get(`${apiUrl}/sidebar-filters/`, {
			headers: {
				'Accept': 'application/json',
				'Content-Type': 'application/json; charset=utf-8',
				'STOREFRONT-CUSTOMER-ACCESS-TOKEN': customerAccessToken,
			}
		})
		.then(res => {
			console.log('filter data-->', JSON.stringify(res.data.results));
			if (res.status === 200) {
				dispatch({
					type: 'SET_PRODUCT_FILTER_DATA',
					payload: res.data.results,
				});
			}
		})
		.catch(err => console.log('ERROR Loading filter data', JSON.stringify(err)));
	};
}

export const setProductVariants = (variants) => {
	return dispatch => {
		dispatch({
			type: 'SET_PRODUCT_VARIANTS',
			payload: variants
		});
	};
}

export const setProductAssignPrint = (assignPrint) => {
	return dispatch => {
		dispatch({
			type: 'SET_PRODUCT_ASSIGN_PRINT',
			payload: assignPrint
		});
	};
}
