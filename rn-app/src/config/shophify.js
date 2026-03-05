import Client from 'shopify-buy';
 
// Initializing a client to return content in the store's primary language
export default client = Client.buildClient({
  domain: 'boboandmusu.myshopify.com',
  storefrontAccessToken: '5247469c1fe5ed4320548cf49eb01d66'
});