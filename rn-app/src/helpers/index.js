import {decode} from 'base64-arraybuffer';

export const validateEmail = email => {
  if(!email){
    return false;
  }else{
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
  }
}

export const validatePassword = password => {
  if(!password){
    return false;
  }else{
    const re = /^(?=.*?[0-9])[A-Za-z0-9@#$!%*?&]{6,}/;
    return re.test(String(password).toLowerCase());
  }
}

export const validateMobileNumber = phone => {
  if(!phone){
    return false;
  }else{
    const re = /^\+[1-9]\d{10,14}$/;
    return re.test(phone);
  }
}

export const capitalizeString = str => {
  let splitStr = str.toLowerCase().split(' ');

  for (let i = 0; i < splitStr.length; i++) {
    splitStr[i] = splitStr[i].charAt(0).toUpperCase() + splitStr[i].substring(1);
  }

  return splitStr.join(' ');
}
