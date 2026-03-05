export default (state = {
  userFingerprints: [],
  fingerprintRequests: [],
  activeFingerprintId: null,
  takenPhoto: null,
  tempFingerPrintData : undefined
}, action) => {
  switch (action.type) {
    case 'RESET_FINGER_PRINTS_STATE':
      state = {
				...state,
        userFingerprints: [],
        fingerprintRequests: [],
        activeFingerprintId: null,
        takenPhoto: null
      }

      break;

    case 'LOADED_FINGER_PRINT_REQUESTS':
      const fingerprintRequests = action.payload;

      if(fingerprintRequests && fingerprintRequests.results){
        state = {
          ...state,
          fingerprintRequests: fingerprintRequests.results 
        }
      }

      break;

    case 'NEW_FINGER_PRINT_REQUEST':
      const newFingerprintRequest = action.payload;

      if(newFingerprintRequest.to_email && customerDetails.email){
        state = {
          ...state,
          fingerprintRequests: [
            ...state.fingerprintRequests,
            newFingerprintRequest
          ]
        }
      }

      break;
  
    case 'LOADED_FINGER_PRINTS':
      const userFingerprints = action.payload.results;

      state = {
        ...state,
        userFingerprints
      }

      break;

    case 'ADDED_FINGER_PRINT':
      state = {
        ...state,
        userFingerprints: [
          ...state.userFingerprints,
          action.payload
        ],
        activeFingerprintId: action.payload.id
      }

      break;

    case 'SET_ACTIVE_FINGER_PRINT_ID': {
      const activeItem = state.userFingerprints.filter(fingerprint => fingerprint.id === action.payload);
      const takenPhoto = (!!activeItem && activeItem.length > 0) ? activeItem[0].photo : null;

      state = {
        ...state,
        activeFingerprintId: action.payload,
        takenPhoto
      }

      break;
    }

    case 'SET_TAKEN_FINGER_PRINT_PHOTO':
      const takenPhoto = action.payload;

      state = {
        ...state,
        takenPhoto
      }

      break;

    case 'SET_TEMP_FINGER_PRINT_DATA':
      const tempFingerPrintData = action.payload;

      state = {
        ...state,
        tempFingerPrintData
      }

      break;

    default:
      break;
  }

  return state;
}