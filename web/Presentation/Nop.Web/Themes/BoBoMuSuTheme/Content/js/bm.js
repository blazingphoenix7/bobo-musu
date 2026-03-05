var bm = {
  addNewPrint: function () {
    if (isMobile.iOS()) {
      var data = {
        actionName: 'addNewPrint',
        returnUrl: window.location.pathname
      }
      window.webkit.messageHandlers.jsHandler.postMessage(JSON.stringify(data));
    }

    if (isMobile.Android()) {
      var data = {
        actionName: 'addNewPrint',
        returnUrl: window.location.pathname
      }

      var myJSONText = JSON.stringify(data);
      Android.takepicture(myJSONText);
    }
  },
  setLoginCustomerId: function (customerId) {
    if (isMobile.iOS()) {
      var data = {
        actionName: 'setLoginCustomerId',
        loginCustomerId: customerId
      }
      console.log(JSON.stringify(data));
      window.webkit.messageHandlers.jsHandler.postMessage(JSON.stringify(data));
    }
  },
  setLogout: function (logoutUrl) {
    if (isMobile.iOS()) {
      var data = {
        actionName: 'setLogout'
      }
      console.log(JSON.stringify(data));
      try {
        window.webkit.messageHandlers.jsHandler.postMessage(JSON.stringify(data));
      } catch (e) {
        console.log(e);
      }
      window.location.href = logoutUrl;
    }
  },
  printPreview: function (productId, form) {
    var postData = {};
    if (form != null)
      postData = this.serializeObject(form);
    postData.productId = productId;
    postData.printId = postData['add-print-to-cart-select'].split(',')[0].split('_')[0]; //todo: will remove printId
    if (isMobile.iOS()) {
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
      if (isMobile.iOS()) {
        var data = {
          actionName: 'getPhoneContacts'
        }
        console.log(JSON.stringify(data));
        window.webkit.messageHandlers.jsHandler.postMessage(JSON.stringify(data));
        bm.saveDebug('getPhoneContacts', JSON.stringify(data));
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
        alert('Failed to save Debug.');
      }
    });
  }
};

var isMobile = {
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
    return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
  }
};