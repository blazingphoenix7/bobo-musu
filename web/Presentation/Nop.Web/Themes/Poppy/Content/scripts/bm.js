var bm = {
  addNewPrint: function () {
    var data = {
      actionName: 'addNewPrint',
      returnUrl: window.location.pathname
    }
    var myJSONText = JSON.stringify(data);
    if (isMobileDevice.iOS()) {
      console.log(myJSONText);
      window.webkit.messageHandlers.jsHandler.postMessage(myJSONText);
    }

    if (isMobileDevice.Android()) {
      newprint.addNewPrint(myJSONText);
    }
  },
  setLoginCustomerId: function (customerId) {
    var data = {
      actionName: 'setLoginCustomerId',
      loginCustomerId: customerId
    }
    var myJSONText = JSON.stringify(data);
    if (isMobileDevice.iOS()) {
      console.log(myJSONText);
      window.webkit.messageHandlers.jsHandler.postMessage(myJSONText);
    }
    if (isMobileDevice.Android()) {
      webview.getLogincustomerID(myJSONText);
    }
  },
  setLogout: function (logoutUrl) {
    if (isMobileDevice.iOS()) {
      var data = {
        actionName: 'setLogout'
      }
      var myJSONText = JSON.stringify(data);

      console.log(myJSONText);
      try {
        window.webkit.messageHandlers.jsHandler.postMessage(myJSONText);
      } catch (e) {
        console.log(e);
      }
      window.location.href = logoutUrl;
    }

    if (isMobileDevice.Android()) {
      webview.setLogout();
    }
  },
  printPreview: function (productId, form) {
    var postData = {};
    if (form != null)
      postData = this.serializeObject(form);
    var selectedPrint = $('option:selected', $('#add-print-to-cart-select'));

    postData.productId = productId;
    postData.printId = postData['add-print-to-cart-select'].split(',')[0].split('_')[0]; //todo: will remove printId
    postData.printImagePath = selectedPrint.attr('data-image-path');
    postData.printThumbnailPath = selectedPrint.attr('data-thumbnail-path');
    if (isMobileDevice.iOS()) {
      var data = {
        actionName: 'printPreview',
        postData: postData
      }
      console.log(JSON.stringify(data));
      window.webkit.messageHandlers.jsHandler.postMessage(JSON.stringify(data));
    }
  },
  getPhoneContacts: function () {
    try {
      if (isMobileDevice.iOS()) {
        var data = {
          actionName: 'getPhoneContacts'
        }
        var myJSONText = JSON.stringify(data);

        console.log(myJSONText);
        window.webkit.messageHandlers.jsHandler.postMessage(myJSONText);
        bm.saveDebug('getPhoneContacts', myJSONText);
      }

      if (isMobileDevice.Android()) {
        message.getPhoneContacts();
      }

    } catch (e) {
      console.log(e);
      bm.saveDebug('getPhoneContacts-Error', e.stack);
    }
  },
  isMobile: function () {
    return isMobile.any();
  },
  serializeObject: function (form) {
    var o = {};
    var a = form.serializeArray();
    $.each(a, function () {
      if (o[this.name]) {
        if (!o[this.name].push) {
          o[this.name] = [o[this.name]];
        }
        o[this.name].push(this.value || '');
      } else {
        o[this.name] = this.value || '';
      }
    });
    return o;
  },

  scrollContent: function (contentElement) {
    var h = 0;
    var fixedElements = $('.element-fixed');
    for (var i = 0; i < fixedElements.length; i++) {
      if ($(fixedElements[i]).length > 0)
        h = h + $(fixedElements[i]).outerHeight();
    }
    var contentHeight = $(window).height() - h;
    /*if (isMobile.iPhoneX()) {
        contentHeight = contentHeight - 50;
    }*/
    $(contentElement).css('height', contentHeight + 'px');
    $(contentElement).addClass('auto-scroll');
  },

  activeMainMenuItem: function () {
    var path = window.location.pathname.toLowerCase();
    $('.main-menu-item-icon').removeClass('active-main-menu-item');
    if (path === "" || path == "/") { // Home
      $('.main-menu-item-icon-home').addClass('active-main-menu-item');
    }
    else if (path.indexOf("/shop") > -1) {
      //$('.main-menu-item-icon-shop').addClass('active-main-menu-item');
      $('.main-menu-item-icon-home').addClass('active-main-menu-item');
    }
    else if (path.indexOf("/print") > -1) {
      $('.main-menu-item-icon-myprints').addClass('active-main-menu-item');
    }
    else if (path.indexOf("/cart") > -1) {
      $('.main-menu-item-icon-cart').addClass('active-main-menu-item');
    }
    else if (path.indexOf("/wishlist") > -1) {
      $('.main-menu-item-icon-wishlist').addClass('active-main-menu-item');
    }
  },

  isEmailAddress: function (s) {
    var mailformat = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
    if (s.match(mailformat)) {
      return true;
    }
    return false;
  },

  saveDebug: function (file, content) {
    content = content + "\n****Browser Info****\n" + navigator.appVersion;
    $.ajax({
      cache: false,
      type: "POST",
      url: "/BMPrint/SaveDebug",
      data: { file: file, content: content },
      success: function () {

      },
      error: function (xhr, ajaxOptions, thrownError) {
        alert(`Failed to save Debug.\n${thrownError}`);
      }
    });
  }
};

var isMobileDevice = {
  Android: function () {
    return navigator.userAgent.match(/Android/i);
  },
  BlackBerry: function () {
    return navigator.userAgent.match(/BlackBerry/i);
  },
  iOS: function () {
    return navigator.userAgent.match(/iPhone|iPad|iPod/i);
  },
  iPhoneX: function () {
    // Get the device pixel ratio
    var ratio = window.devicePixelRatio || 1;
    // Define the users device screen dimensions
    var screen = {
      width: window.screen.width * ratio,
      height: window.screen.height * ratio
    };
    if (this.iOS() && screen.width == 1125 && screen.height === 2436) {
      return true;
    }
    return false;
  },
  Opera: function () {
    return navigator.userAgent.match(/Opera Mini/i);
  },
  Windows: function () {
    return navigator.userAgent.match(/IEMobile/i);
  },
  any: function () {
    return (isMobileDevice.Android() || isMobileDevice.BlackBerry() || isMobileDevice.iOS() || isMobileDevice.Opera() || isMobileDevice.Windows());
  }
};