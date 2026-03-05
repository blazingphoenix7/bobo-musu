export default(state = {
  orders: [],
  checkoutWebUrl: null,
  checkOutId : undefined,
  cartCount : 0
}, action) => {
	switch(action.type){
    case 'RESET_ORDERS_STATE':
      state = {
				...state,
        orders: [],
        checkoutWebUrl: null,
        checkOutId : undefined,
        cartCount : 0
      }

      break;

    case 'LOADED_CUSTOMER_ORDERS':
      // const edges = action.payload?.data?.customer?.orders?.edges;

      // if(edges){
      //   let orders = [];
      //   edges.map(order => {

      //       if(order?.node?.lineItems?.edges){
      //         order?.node?.lineItems?.edges?.map((item) => {
      //           let fingerprintName = item?.node?.customAttributes?.find(x => x.key == "Fingerprint Title") || ''
      //           orders.push({
      //             id: order.node.id,
      //             name: order.node.name,
      //             orderNumber: order.node.orderNumber,
      //             title : item.node.title,
      //             price: item.node.originalUnitPriceSet.presentmentMoney.amount,
      //             fulfillmentStatus: order.node.displayFulfillmentStatus ,
      //             image: item.node.image.transformedSrc,
      //             // variant : item.node.variant.selectedOptions,
      //             variant : item?.node?.customAttributes || [],
      //             description : item.node.product.description,
      //             fingerprintName : fingerprintName.value,
      //           });
      //         })
      //       }

      //     // return ({
      //     //   id: order.node.id,
      //     //   name: order.node.name,
      //     //   orderNumber: order.node.orderNumber,
      //     //   price: order.node.subtotalPriceSet.presentmentMoney.amount,
      //     //   fulfillmentStatus: order.node.lineItems.edges[0].node.fulfillmentStatus,
      //     //   image: order.node.lineItems.edges[0].node.image.transformedSrc
      //     // })
      //   });

      //   state = {
      //     ...state,
      //     orders
      //   }
      // }

      const edges = action.payload;

      if(edges){
        let orders = [];
        edges.map(order => {
          order.line_items.map(lineItem => {
            let fingerprintName =
            lineItem.properties?.find(
                x => x.name == 'Fingerprint Title',
              ) || '';
            orders.push({
              orderData: order,
              id: order?.id,
              name: lineItem?.name,
              orderNumber: order?.order_number,
              title: lineItem?.name,
              price: lineItem?.price, 
              fulfillmentStatus: lineItem?.fulfillment_status,
              image: lineItem?.images[0]?.src,
              // variant : item.node.variant.selectedOptions,
              variant: lineItem?.properties || [],
              description: lineItem?.description,
              fingerprintName: fingerprintName.value,
            });
          });
        });

          state = {
          ...state,
          orders
        }
      }

      break;

    case 'SET_CHECKOUT_WEB_URL':
      state = {
        ...state,
        checkoutWebUrl: action.payload
      }
      break;
    case 'SET_CHECKOUT_ID':
      state = {
        ...state,
        checkOutId: action.payload
      }
      break;
    case 'SET_CART_COUNT':
      state = {
        ...state,
        cartCount: action.payload
      }
      break;
    case 'SET_FULFILLMENT_DATA':
        state = {
          ...state,
          fulfillmentData: action.payload
        }
        break;

		default:
			break;
	}

	return state;
}