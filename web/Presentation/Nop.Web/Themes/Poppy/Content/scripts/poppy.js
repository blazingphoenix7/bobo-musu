(function ($, ssCore, ssEx) {

    window.themeSettings = {
        themeBreakpoint: 1000,
        isAccordionMenu: false
    }

    var overrideMegaMenuDropDownClick = function () {
        var megaMenu = $('.mega-menu');

        var megaMenuClick = "click.megaMenuEvent";
        var megaMenuDocumentClick = "click.megaMenuDocumentEvent";

        if (megaMenu.attr('data-enableClickForDropDown') === 'true') {
            var megaMenuDropDowns = $(".mega-menu > li > .dropdown, .mega-menu > li > .sublist-wrap");
            megaMenuDropDowns.siblings("a").on('click', function (e) {
                e.preventDefault();
            });

            megaMenuDropDowns.click(function (e) {
                e.stopPropagation();
            });

            // open/close dropdowns
            megaMenu.children('li').off(megaMenuClick).on(megaMenuClick, function (e) {
                e.stopPropagation();

                var currentDropdown = $(this).children(".dropdown, .sublist-wrap");
                megaMenuDropDowns.not(currentDropdown).removeClass('active'); // Hides all visible dropdowns except the current one

                currentDropdown.addClass('active');
            });

            // close opened dropdown
            $(document).off(megaMenuDocumentClick).on(megaMenuDocumentClick, function () {
                megaMenuDropDowns.removeClass('active');
            });
        }
    };

    var isSaleOfTheDayInitialized = false;

    var initializeSaleOfTheDayCarousels = function () {
        if (isSaleOfTheDayInitialized) {
            return;
        }

        $('.sale-of-the-day-offer .owl-carousel').not('.initialized').each(function () {
            var that = $(this);

            if (that.find('.product-element').length > 1) {
                that.owlCarousel({
                    rtl: $('.sale-of-the-day-offer.support-rtl').length > 0,
                    loop: true,
                    margin: 0,
                    nav: false,
                    items: 1,
                    //autoHeight: true,
                    autoplay: true,
                    autoplayTimeout: 5000,
                    autoplayHoverPause: true,
                    onInitialized: function () {
                        that.addClass('initialized');
                    }
                });
            }

            that.children('.owl-controls').appendTo($(that).parents('.sale-of-the-day-offer').children('.panel-header'));
        });
    };

    $(document).ready(function () {
        var responsiveAppSettings = {
            isEnabled: true,
            themeBreakpoint: window.themeSettings.themeBreakpoint,
            isSearchBoxDetachable: true,
            isHeaderLinksWrapperDetachable: false,
            doesDesktopHeaderMenuStick: false,
            doesScrollAfterFiltration: false,
            doesSublistHasIndent: true,
            displayGoToTop: true,
            hasStickyNav: true,
            lazyLoadImages: $('body').hasClass('lazy-load-images'),
            selectors: {
                menuTitle: ".menu-title",
                headerMenu: ".header-menu",
                closeMenu: ".close-menu",
                movedElements: ".admin-header-links, .header, .responsive-nav-wrapper, .master-wrapper-content, .slider-wrapper, .footer",
                sublist: ".header-menu .sublist",
                overlayOffCanvas: ".overlayOffCanvas",
                withSubcategories: ".with-subcategories",
                filtersContainer: ".nopAjaxFilters7Spikes",
                filtersOpener: ".filters-button span",
                searchBoxOpener: ".search-wrap > span",
                searchBox: ".store-search-box",
                searchBoxBefore: ".header-links",
                navWrapper: ".responsive-nav-wrapper",
                navWrapperParent: ".responsive-nav-wrapper-parent",
                headerLinksOpener: "#header-links-opener",
                headerLinksWrapper: ".header-links-wrapper",
                //headerLinksWrapperMobileInsertAfter: ".header",
                //headerLinksWrapperDesktopPrependTo: ".header",
                shoppingCartLink: ".shopping-cart-link"
            }
        };

        if (ssCore.isMobileDevice) {
            //mobile/desktop class functionality for the body tag
            $('body').removeClass('desktop').addClass('mobile');

            initializeSaleOfTheDayCarousels();

            //activate the mobile specific custom select functionality
            mobileCustomSelect('select');
            $('.opc .button-1').on('click', function () {
                $(document).ajaxSuccess(function () {
                    mobileCustomSelect('.opc select');
                });
            });

            $('.checkout-page').on('click', '.payment-details label', function () {
                setTimeout(function () {
                    mobileCustomSelect('.payment-info select');
                });
            });

            // activate the mobileSelect for SmartProductCollections
            // when the whole panel has loaded
            $(window).on('newProductsAddedToPageEvent', function () {
                mobileCustomSelect('.spc select');
            });

            // append the goToTop button inside responsive-nav-wrapper if the navigation position is bottom
            if ($('body').hasClass('nav-bottom')) {
                $('#goToTop').appendTo('.responsive-nav-wrapper');
            }

            // Use the device's back button to close all mobile navigations, to establish more of an app feel to the UX 
            // CURRENTLY DISABLED!!!
            // mobileBackButtonClose();

            // initializing the subCategorySelect url change, so that when an option is selected
            // the user is taken to the respective SubCategory's page
            subCategorySelect();

            // initializing the mobileAccountNavigation url change, so that when an option is selected
            // the user is taken to the respective account page
            mobileAccountNavigation();

            // AJAXFILTERS SPECIFIC FIX
            if ($('.nopAjaxFilters7Spikes').length > 0) {
                ajaxFiltersRefreshSelectText();
            }

            // fixes the doubled input and label removeFromCart by footable
            // to be properly executed when selected
            $(window).on('footableRowOpened', function () {
                footableInputLabelRemoveFromCartFix();
            });
        }
        else {
            $(document).on('themeBreakpointPassed7Spikes', function (e) {

                if (e.isMobileResolution) {
                    // mobile/desktop class functionality for the body tag
                    $('body').removeClass('desktop').addClass('mobile');

                    initializeSaleOfTheDayCarousels();

                    // remove the desktop specific custom select fucntionality
                    $('select').each(function () {
                        if ($(this).next().children('.select-options').length > 0) {
                            $(this).selectbox('detach').unwrap();
                        }
                    });

                    // append the goToTop button inside responsive-nav-wrapper if the navigation position is bottom
                    if ($('body').hasClass('nav-bottom')) {
                        $('#goToTop').appendTo('.responsive-nav-wrapper');
                    }

                    // activate the mobile specific custom select element
                    mobileCustomSelect('select');
                    $('.opc .button-1').on('click', function () {
                        $(document).ajaxSuccess(function () {
                            mobileCustomSelect('.opc select');
                        });
                    });

                    $('.checkout-page').on('click', '.payment-details label', function () {
                        setTimeout(function () {
                            mobileCustomSelect('.payment-info select');
                        });
                    });

                    // activate the mobileSelect for SmartProductCollections
                    // when the whole panel has loaded
                    $(window).on('newProductsAddedToPageEvent', function () {
                        mobileCustomSelect('.spc select');
                    });

                    // header-menu DOM position change
                    $('.header-menu').insertAfter('.responsive-nav-wrapper-parent');

                    $('.admin-header-links, .header, .responsive-nav-wrapper, .master-wrapper-content, .slider-wrapper, .footer').removeClass('move-right');

                    // initializing the subCategorySelect url change, so that when an option is selected
                    // the user is taken to the respective SubCategory's page
                    subCategorySelect();

                    // initializing the mobileAccountNavigation url change, so that when an option is selected
                    // the user is taken to the respective account page
                    mobileAccountNavigation();

                    // AJAXFILTERS SPECIFIC FIX
                    if ($('.nopAjaxFilters7Spikes').length > 0) {
                        ajaxFiltersRefreshSelectText();
                    }

                    // fixes the doubled input and label removeFromCart by footable
                    // to be properly executed when selected
                    $(window).on('footableRowOpened', function () {
                        footableInputLabelRemoveFromCartFix();
                    });
                }
                else {
                    // mobile/desktop class functionality for the body tag
                    $('body').removeClass('mobile').addClass('desktop');

                    initializeSaleOfTheDayCarousels();

                    // return the goToTop button inside the body tag
                    $('#goToTop').appendTo('body');

                    // wrap the sublist element with a wrapper for the desktop menu effect
                    if (!$('.header-menu .sublist').parent().hasClass('sublist-content')) {
                        $('.header-menu .sublist').wrap('<div class="sublist-content"></div>');
                    }

                    // remove the mobile specific custom select functionality element
                    $('select ~ .select-box').remove();

                    // header-menu DOM position change
                    $('.header-menu').insertAfter('.header-logo');

                    // add a hover effect to the header-footer social-sharing background line
                    $('.social-sharing li').hover(function () {
                        if ($(this).index() < 5)
                            $(this).parent().toggleClass('hoverBefore');
                        else
                            $(this).parent().toggleClass('hoverAfter');
                    });

                    // activate the desktop specific custom select functionality and attach a custom scroll if needed
                    // the desktopCustomSelect function works ONLY with a string for parameter!
                    desktopCustomSelect('select');
                    $('.opc .button-1').on('click', function () {
                        $(document).ajaxSuccess(function () {
                            desktopCustomSelect('.opc select');
                        });
                    });

                    $('.checkout-page').on('click', '.payment-details label', function () {
                        setTimeout(function () {
                            desktopCustomSelect('.payment-info select');
                        });
                    });

                    if ($('.ropc').length === 0) {
                        $(document).on("addressStatesUpdated", function (e) {
                            $(e.statesDropdownId).selectbox("detach");
                            desktopCustomSelect(e.statesDropdownId);
                        });
                    }

                    $(window).on('nopAjaxCartButtonsAddedEvent', function () {
                        desktopCustomSelect('.item-box select');
                    });

                    // AJAXFILTERS SPECIFIC FIX
                    if ($('.nopAjaxFilters7Spikes').length > 0) {
                        ajaxFiltersRefreshSelectText();
                        ajaxFiltersDisabledSelectsApplication()
                    }

                    $.event.trigger("poppyThemeDesktopClassAdded");
                }

                $('.cart-collaterals').toggleClass('for-mobile', $('body').hasClass('mobile'));

                if ($('body').hasClass('product-details-page-body')) {

                    //resize tabs
                    quickTabsSlider.onResize();
                }
            });

            // DO STUFF after the QuickView modal window is loaded
            $(document).on('nopQuickViewDataShownEvent', function () {
                $('.quickView').addClass('opened');
                desktopCustomSelect('.quickView select');
                handleProductPageThumbs();
            });

            // DO STUFF after the AjaxCart modal window is loaded
            $(document).on('nopAjaxCartMiniProductDetailsViewShown', function () {
                desktopCustomSelect('.ajaxCart select');
            });

            // this is the custom animation of the searchBox
            desktopSearchBoxFunc();
        }

        // code for ProductPage only!
        if ($('.page').hasClass('product-details-page')) {

            $('.bottom-section').each(function () {
                if ($('.giftcard', this).length > 0 || $('.rental-attributes', this).length > 0) {
                    $(this).addClass('with-gift-card');
                }
            });

        }

        // adds click event to the shipping and discount blocks on ShoppingCartPage
        $('.deals-title, .est-ship-title', '.cart-collaterals').on('click', function () {
            if ($('body').hasClass('mobile')) {
                var that = $(this);
                that.next().slideToggle();
            }
        });

        overrideMegaMenuDropDownClick();
        addPlusMinusQty();
        handleProductPageThumbs();
        inputsRequiredDesignFix();
        ssCore.loadImagesOnScroll();

        // dynamically added functionalities and fixes for our RealOnePageCheckout
        $(window).on('nopOnePageCheckoutPanelsLoadedEvent', function () {
            inputsRequiredDesignFix();
        });

        ssEx.initResponsiveTheme(responsiveAppSettings);
    });

    if ($('body').hasClass('product-details-page-body')) {

        $(document).on('quickTabsCreated', function () {

            quickTabsSlider.init();
        });
    }

    $(document).on('poppyThemeDesktopClassAdded', function () {
        headerMenuScrollHelper();
    });

    $(window).on('load', function () {

        productListButtonsPositioning();
        desktopFilterOpenButton();

        // this function ensures that no matter the height of the header
        // it would always be visible via scrolling the website


        //if ($('body').hasClass('desktop')) {
        //    debugger;
        //}

        // initializing the custom share buttons on the product page
        if ($('body').hasClass('product-details-page-body')) {
            productShareButtonsPreparation();

            // initializing the custom slider functionality for the QuickTabs plug-in
            quickTabsSlider.init();
        }

        if ($('body').hasClass('blog-pages-body')) {
            blogNavigatioPreparation();
            if (typeof Masonry != "undefined") { // not included on mobile
                $('.blog-posts').masonry({
                    columnWidth: '.sizer',
                    itemSelector: '.post',
                    percentPosition: true,
                    gutter: 30
                });
            }

        }

        // masonry grid initialization
        if ($('body').hasClass('news-pages-body')) {
            if (typeof Masonry != "undefined") { // not included on mobile
                $('.news-items').masonry({
                    columnWidth: '.sizer',
                    itemSelector: '.news-item',
                    percentPosition: true,
                    gutter: 30
                });
            }
        }

        // apply scroll to MegaMenu dropdown element
        $('.with-sublist-wrap').hover(function () {
            if (!$(this).children('.dropdown').hasClass('.ps-container')) {
                $(this).children('.dropdown').perfectScrollbar({
                    swipePropagation: false,
                    wheelSpeed: 2,
                    suppressScrollX: true
                });
            }
        });

        // hide the pageLoading effect
        $('.page-loader-effect').fadeOut(200);
    });

    $(window).on('load resize', function (e) {

        if ($(window).width() > 767) {
            $('.gallery').insertBefore('.overview');

            $(window).on('newProductsAddedToPageEvent', function () {
                $('.spc-categories .item-box').each(function () {
                    var btnsWrap = $('.buttons', $(this));
                    var additionalBtns = $('.additional-buttons', $(this));

                    additionalBtns.appendTo(btnsWrap);
                });
            });
        }
        else {
            $('.gallery').appendTo('.gallery-wrap');
        }

        // Sale of the Day specific script!!!
        if ($('.sale-of-the-day-offer').length > 0) {
            saleOfTheDayRearrange();
        }

        if ($('body').hasClass('desktop')) {
            addressesPageBodyHeight();
        }
    });

    $(window).on('resize orientationchange', function () {

        if ($('body').hasClass('product-details-page-body')) {
            quickTabsSlider.onResize();
        }

        $('.spc-categories .item-box').each(function () {
            var btnsWrap = $('.buttons', $(this));
            var additionalBtns = $('.additional-buttons', $(this));

            additionalBtns.appendTo(btnsWrap);
        });

    });

    // AjaxFilters specific additional buttons positiong on request success
    $(window).on('nopAjaxFiltersFiltrationCompleteEvent', function () {
        productListButtonsPositioning()
    })



    // FUNCTIONS

    function headerMenuScrollHelper() {

        var windowHeight = $(window).outerHeight();
        var header = $('.header');
        var headerHeight = header.outerHeight();
        
        if (headerHeight != windowHeight) {

            var windowBottom = $(window).scrollTop() + $(window).outerHeight();

            header.addClass('stick-enabled');

            if (headerHeight < windowBottom) {
                header.addClass('stick-bottom');
            }

            $(window).on('scroll', function () {

                windowBottom = $(window).scrollTop() + $(window).outerHeight();

                if (headerHeight < windowBottom) {
                    header.addClass('stick-bottom');
                }
                else {
                    header.removeClass('stick-bottom');
                }

            });
        }

        // prevent scrolling inside the header menu on desktop from bubbling

        $('.header > .header-menu').on('scroll mousewheel wheel DOMMouseScroll', function (e) {
            var delta = e.originalEvent.wheelDelta || -e.originalEvent.detail;

            if (delta > 0 && $(this).scrollTop() <= 0)
                return false;
            if (delta < 0 && $(this).scrollTop() >= this.scrollHeight - $(this).outerHeight())
                return false;

            return true;
        });

    }

    function desktopSearchBoxFunc() {

        // open/close search box on click of the button, also close it by clicking anywhere on the page

        var openSearchFormButton = $('.btn-open-search');
        var searchBox = $('.search-box');
        var searchBoxForm = $('.search-box form');
        var overflowResetValue = 'overflow-initial';

        openSearchFormButton.on('click', function (e) {
            e.stopPropagation();
            searchBox.toggleClass('opened');

            if (searchBoxForm.hasClass(overflowResetValue)) {
                searchBoxForm.removeClass(overflowResetValue);
            }
            else {
                searchBoxForm.delay(300).queue(function (a) {
                    $(this).addClass(overflowResetValue);
                    a();
                });
            }
        });
        $(document).on('click', function () {
            searchBox.removeClass('opened');
            searchBoxForm.removeClass(overflowResetValue);
        });
        searchBox.on('click', function (e) {
            e.stopPropagation();
        });

        if ($('.search-box-content select').length > 0) {
            searchBox.addClass('with-select');
        }

    }

    function incrementQuantityValue(event) {
        event.preventDefault();
        event.stopPropagation();

        var input = $(this).siblings('.qty-input, .productQuantityTextBox').first();

        var value = parseInt(input.val());
        if (isNaN(value)) {
            input.val(1);
            return;
        }

        value++;
        input.val(value);

        //http://stackoverflow.com/a/17110709/6744066
        input.trigger('input'); //input event trigger required by ROPC
        input.trigger('change'); //change event trigger required by IE11
    }

    function decrementQuantityValue(event) {
        event.preventDefault();
        event.stopPropagation();

        var input = $(this).siblings('.qty-input, .productQuantityTextBox').first();

        var value = parseInt(input.val());

        if (isNaN(value)) {
            input.val(1);
            return;
        }

        if (value <= 1) {
            return;
        }

        value--;
        input.val(value);

        //http://stackoverflow.com/a/17110709/6744066
        input.trigger('input'); //input event trigger required by ROPC
        input.trigger('change'); //change event trigger required by IE11
    }

    function addPlusMinusQty() {

        // Normal & Ajax Cart
        $(document).on('click', '.item-box .plus', incrementQuantityValue).on('click', '.item-box .minus', decrementQuantityValue);
        $(document).on('click', '.ajaxCart .plus', incrementQuantityValue).on('click', '.ajaxCart .minus', decrementQuantityValue);
        $('.variant-overview').on('click', '.plus', incrementQuantityValue).on('click', '.minus', decrementQuantityValue);

        // Home Page Categories Tabs Normal & Ajax Cart
        $('.home-page-category-tabs').on('click', '.plus', incrementQuantityValue).on('click', '.minus', decrementQuantityValue);

        // Quick View
        $(document).on('click', '.quickView .plus', incrementQuantityValue).on('click', '.quickView .minus', decrementQuantityValue);

        // product Details Page
        $('.product-essential .plus').on('click', incrementQuantityValue);
        $('.product-essential .minus').on('click', decrementQuantityValue);

        // shopping cart page table qty-input
        // made with event delegation, because of Angular
        $('.wishlist-page, .shopping-cart-page, .ropc-page').on('click', '.cart .plus', incrementQuantityValue).on('click', '.cart .minus', decrementQuantityValue);

    }

    function subCategorySelect() {

        $('.sub-category-select').on('change', function () {

            window.location.href = $(this).val();

        });

    }

    function productListButtonsPositioning() {

        var additionalButtons, itemBoxButtons;

        $('.product-list .item-box').each(function () {

            additionalButtons = $('.additional-buttons', $(this));
            itemBoxButtons = $('.buttons', $(this));

            additionalButtons.appendTo(itemBoxButtons);

        });

    }

    function desktopFilterOpenButton() {

        $('.header .desktop-filters-button').hover(function (e) {

            $('.nopAjaxFilters7Spikes').toggleClass('open');

            $('.nopAjaxFilters7Spikes').perfectScrollbar({
                swipePropagation: false,
                wheelSpeed: 2,
                suppressScrollX: true
            });

        });

        $(document).on('mouseleave', '.nopAjaxFilters7Spikes', function (e) {

            $('.nopAjaxFilters7Spikes').perfectScrollbar('destroy');

        });

    }

    function productShareButtonsPreparation() {
        var pageUrl = window.location.href;
        var imgUrl = $('.gallery .picture img').attr('src');
        var descString = $('.full-description').length > 0 ? $('.full-description').text() : $('.short-description').text();

        function openWindow(url) {
            window.open(url, 'newwindow', 'width=' + 640 + ', height=' + 480 + ', top=' + 0 + ', left=' + 0);
        }
        $('ul.networks-list li.network-item a').click(function (e) {
            e.preventDefault();
            return openWindow(this.href);
        });

        $('#twitter-share').attr('href', ('https://twitter.com/share?url=' + pageUrl));
        $('#pinterest-share').attr('href', "http://pinterest.com/pin/create/button/?url=" + pageUrl + "&media=" + imgUrl + "&description=" + descString);
        $('#facebook-share').attr('href', ('https://www.facebook.com/sharer.php?u=' + pageUrl));
        $('#google-share').attr('href', ('https://plus.google.com/share?url=' + pageUrl));
        $('#linkedin-share').attr('href', ('https://www.linkedin.com/shareArticle?mini=true&url=' + pageUrl));
        $('#reddit-share').attr('href', ('https://reddit.com/submit?url=' + pageUrl));
    }

    function handleProductPageThumbs(gallerySelector) {
        var thumbInfoSelector = '.cloudzoom-gallery, .thumb-popup-link, .thumb-item';
        var thumbParentSelector = gallerySelector || '.gallery, .item-gallery';
        var galleries = $(thumbParentSelector);

        var navigationArrowClickHandler = function () {
            var that = $(this);
            var fullSizeImageUrl = that.find('img').attr('data-fullSizeImageUrl');

            that.trigger('mouseenter');

            var correspondingThumb = that.closest('.product-essential, .product-element')
                                            .find(thumbParentSelector)
                                                .find(thumbInfoSelector)
                                                    .filter('[href="' + fullSizeImageUrl + '"]');

            if (correspondingThumb.hasClass('cloudzoom-gallery')) {
                correspondingThumb.click();
            }
            else {
                $.event.trigger({
                    type: 'nopMainProductImageChanged',
                    target: that,
                    pictureDefaultSizeUrl: fullSizeImageUrl,
                    pictureFullSizeUrl: fullSizeImageUrl
                });
            }
        };

        var setPreviousNavigationImage = function (thumbInfoParent) {
            var thumbInfos = thumbInfoParent.find(thumbInfoSelector);
            var target = thumbInfos.filter('.active').prev(thumbInfoSelector);

            if (target.length === 0) {
                target = thumbInfos.last();
            }

            $(thumbInfoParent).find('.picture-thumbs-prev-arrow img')
                                .attr('src', target.find('img').attr('src'))
                                    .attr('data-fullSizeImageUrl', target.attr('href'))
                                        .attr('alt', target.find('img').attr('alt'));
        };

        var setNextNavigationImage = function (thumbInfoParent) {
            var thumbInfos = thumbInfoParent.find(thumbInfoSelector);
            var target = thumbInfos.filter('.active').next(thumbInfoSelector);

            if (target.length === 0) {
                target = thumbInfos.first();
            }

            $(thumbInfoParent).find('.picture-thumbs-next-arrow img')
                                .attr('src', target.find('img').attr('src'))
                                    .attr('data-fullSizeImageUrl', target.attr('href'))
                                        .attr('alt', target.find('img').attr('alt'));
        };

        galleries.each(function () {
            var thisParent = $(this);
            var thumbInfos = thisParent.find(thumbInfoSelector);

            thumbInfos.first().addClass('active');
        });

        // Previous arrow
        galleries.find('.picture-thumbs-prev-arrow').on('mouseenter', function () {
            setPreviousNavigationImage($(this).closest(thumbParentSelector));

            $(this).addClass('hovered');
        })
            .on('mouseleave', function () {
                $(this).removeClass('hovered');
            })
            .on('click', navigationArrowClickHandler);

        // Next arrow
        galleries.find('.picture-thumbs-next-arrow').on('mouseenter', function () {
            setNextNavigationImage($(this).closest(thumbParentSelector));

            $(this).addClass('hovered');
        })
            .on('mouseleave', function () {
                $(this).removeClass('hovered');
            })
            .on('click', navigationArrowClickHandler);

        // Product Thumbs
        $('.thumb-popup-link, .cloudzoom-gallery', thumbParentSelector).on('click', function (e) {
            var that = $(this);
            var fullImageUrl = that.attr('href');

            e.preventDefault();

            $.event.trigger({
                type: 'nopMainProductImageChanged',
                target: that,
                pictureDefaultSizeUrl: fullImageUrl,
                pictureFullSizeUrl: fullImageUrl
            });
        });

        $(document).on('nopMainProductImageChanged', function (e) {
            var thumbInfoParent = $(e.target).closest('.product-essential, .product-element').find(thumbParentSelector);
            var correspondingThumb = thumbInfoParent.find(thumbInfoSelector).filter('[href="' + e.pictureFullSizeUrl + '"]');

            if (correspondingThumb.length === 0) {
                return;
            }

            thumbInfoParent.find('.picture a[id^="main-product-img-lightbox-anchor"]').attr('href', e.pictureFullSizeUrl);
            thumbInfoParent.find('#cloudZoomImage, .picture img[id^="main-product-img"], .item-picture > a > img').attr('src', e.pictureDefaultSizeUrl);

            correspondingThumb.addClass('active').siblings(thumbInfoSelector).removeClass('active');

            setPreviousNavigationImage(thumbInfoParent);
            setNextNavigationImage(thumbInfoParent);
        });
    }

    function inputsRequiredDesignFix() {

        $('.inputs').each(function () {

            if ($(this).children('.required').length > 0) {

                $(this).addClass('is-required');

            }

        });

    }

    function saleOfTheDayRearrange() {

        //on mobile (by default!) the Gallery needs to be on top of the Overview
        //on desktop (after 1366!) the styling changes to a table layout, so we need the gallery after the overview in the DOM
        $('.sale-of-the-day-offer .panel-item').each(function () {
            var gallery = $('.item-gallery', $(this));
            var overview = $('.item-overview', $(this))

            if (ssCore.getViewPort().width >= 1366) {
                gallery.insertAfter(overview);
            }
            else {
                overview.insertAfter(gallery);
            }
        });

    }

    function desktopCustomSelect(selects) {

        $(selects).not('.ropc select').each(function () {

            //this check is used for select elements that appear in the DOM dinamically 
            //i.e. OnePageCheckout AJAX loaded content!
            if ($(this).next().hasClass('select-box')) { return }

            //initialization of the selectBox and also the perfectScrollbar when needed
            $(this).selectbox('attach')
                    .next()
                     .on('click', function () {
                         var sbOptions = $('.select-options', this);

                         //the PerfectScrollbar doesn't work properly on elements with top and bottom padding
                         //that's why before we initiate it, we need to wrap the content of the dropdown in another div
                         //since we initiate the PerfectScrollbar on .sbOptions, we set the top and bottom padding on the new .sbOptions-content
                         if (!sbOptions.children('.select-options-content').length > 0) {
                             sbOptions.children().wrapAll('<div class="select-options-content"></div>');
                         }

                         //the setTimeout serves as a buffer, because approximately 200ms is the time it takes for the dropdown to fully open
                         //after it opens, the script of the PerfectScrollbar takes the full height (outerHeight) of the dropdown, to initiate properly
                         //currently the CSS sets the max-height of the dropdown to be 182px, and that's where the 181 magic number comes from
                         setTimeout(function () {
                             if (sbOptions.outerHeight() > 192 && !sbOptions.hasClass('ps-active-y')) {
                                 sbOptions.perfectScrollbar({
                                     minScrollbarLength: 20,
                                     suppressScrollX: true
                                 });
                             }
                         }, 200);
                     });

            if ($(this).parent().closest('div').hasClass('select-wrap')) { return }

            $(this).add($(this).next()).wrapAll('<div class="select-wrap"></div>')

        });

    }

    function mobileCustomSelect(selects) {

        $(selects).not('.ropc select').each(function () {

            if ($(this).parent().closest('div').hasClass('select-wrap')) {
                return;
            }

            $(this).simpleSelect();
        });

    }

    function mobileAccountNavigation() {

        var mobileAccountNav = $('.mobile-account-nav');

        $('option', mobileAccountNav).each(function () {

            if ($(this).attr('data-href') == window.location.pathname) {

                // asures that the select always knows the selected value
                // and doesn't break the first value
                $(this).attr('selected', 'selected');

                // asures that the page you are on is reflected in the custom select
                mobileAccountNav.next().find('.select-inner').text($(this).val());

            }

        });

        mobileAccountNav.on('change', function () {

            var that = $(this);

            $('option', this).each(function () {
                if (that.val() == $(this).val()) {
                    window.location.pathname = $(this).attr('data-href');
                }
            });

        });

    }

    function addressesPageBodyHeight() {

        var blockAccountNavigation = $('.block-account-navigation');
        var listItem = $('.list-item', blockAccountNavigation);
        var listItemHeight = listItem.outerHeight();
        var listItemMarginTop = parseInt($(listItem[1]).css('margin-top')); // select the second child because the first doesn't have margin-top
        var listItemCount = listItem.length;
        var addressesPageBodyHeight = (listItemCount * listItemHeight) +
                                        ((listItemCount - 1) * listItemMarginTop) +
                                            (parseInt(blockAccountNavigation.css('top')) * 2);// multiply the top value, to asure the bottom space equals the top

        $('.account-page .page-body').css('min-height', addressesPageBodyHeight);
    }

    function blogNavigatioPreparation() {

        var navigationWrap = $('.blog-navigation-wrap');
        var navigation = $('.blog-navigation');
        var yearNumber = $('.year .number');
        var desktopBlogNavButton = $('.desktop-blog-options-button');
        var mobileBlogNavButton = $('.mobile-blog-options-button');
        var overlayOffCanvas = $('.overlayOffCanvas');
        var btnClose = $('.blog-navigation-wrap .btn-close');
        var blogSearchAutocomplete = $('.blog-instant-search');

        // desktop and mobile
        yearNumber.on('click', function () {
            $(this)
                .toggleClass('opened')
                    .next()
                        .slideToggle();
        });

        // mobile only
        mobileBlogNavButton.on('click', function () {
            navigationWrap.toggleClass('active');
            overlayOffCanvas.addClass('show').fadeIn();
        });
        overlayOffCanvas.on('click', function () {
            navigationWrap.removeClass('active');
            $(this).removeClass('show');
        });
        btnClose.on('click', function () {
            navigationWrap.toggleClass('active');
            overlayOffCanvas.fadeOut().addClass('show');
        });

        // desktop only
        desktopBlogNavButton.hover(function () {
            navigationWrap.toggleClass('active').stop(true, true);
        });

        // prevent scroll from bubbling up
        navigationWrap.on('scroll mousewheel wheel DOMMouseScroll', function (e) {
            var delta = e.originalEvent.wheelDelta || -e.originalEvent.detail;

            if (delta > 0 && $(this).scrollTop() <= 0)
                return false;
            if (delta < 0 && $(this).scrollTop() >= this.scrollHeight - $(this).outerHeight())
                return false;

            return true;
        });

    }

    function ajaxFiltersRefreshSelectText() {

        // filtersLoaded is used to asure that the whole code inside the IF statement
        // executes only once on document ready, and not on every filtration
        var filtersLoaded = true;

        // Set the first option text to the sbSelector element
        $('.filter-block').on('click', '.clearFilterOptions', function () {

            var selectParent = $(this).parent().next();
            var firstOptionText = selectParent.find('select option:first-child').text();

            selectParent.find('.select-inner').text(firstOptionText)

        });

        $(document).on('nopAjaxFiltersFiltrationCompleteEvent', function () {
            if (filtersLoaded) {
                // go through all filter-block panels
                // then go through all options in each filter-block selects
                // if there is an option than IS selected, than the sbSelector element changes
                // its text ot the text of the selected option
                $('.filter-block').each(function () {

                    var thisFilterBlock = $(this);
                    var filterSelect = thisFilterBlock.find('select');

                    $('option', filterSelect).each(function () {

                        var thisOption = $(this);

                        if (thisOption.attr('selected') == 'selected') {

                            thisFilterBlock.find('.select-inner').text(thisOption.text())

                        }

                    });

                });

                // change to false to stop the code from executing more than on LOAD
                filtersLoaded = false;
            }
        });

    }

    function ajaxFiltersDisabledSelectsApplication() {

        // this function is used to apply disabled states to the custom selects' options
        // whenever the native selects receive disabled state for any of theirs
        // on every filtration, including refresh/load of the page

        $(document).on('nopAjaxFiltersFiltrationCompleteEvent', function () {

            $('.filter-block').each(function () {

                var thisFilterBlock = $(this);
                var filterSelect = thisFilterBlock.find('select');

                $('option', filterSelect).each(function () {

                    var thisOption = $(this);
                    var thisOptionValAttr = thisOption.attr('value');

                    thisFilterBlock.find('.sbOptions-item').each(function () {

                        var thisSbOptionsItem = $(this);
                        var sbOptionsItemAnchor = $('a', thisSbOptionsItem);

                        thisSbOptionsItem.removeClass('disabled');

                        if (thisOption.attr('disabled') == 'disabled' && thisOptionValAttr == sbOptionsItemAnchor.attr('rel')) {
                            thisSbOptionsItem.addClass('disabled');
                        }

                    });

                });

            });

        });

    }

    function footableInputLabelRemoveFromCartFix() {

        $('.footable-row-detail').each(function () {

            var rowDetail = $(this);

            if (!rowDetail.hasClass('checkboxIDChanged')) {

                var removeForCartInput = $('input[name=removefromcart]', rowDetail);
                var removeForCartInputID = removeForCartInput.attr('id');
                var addToCartInput = $('input[name=addtocart]', rowDetail);
                var addToCartInputID = addToCartInput.attr('id');

                // for input[name=removefromcart]
                $('label[for=' + removeForCartInputID + ']').attr('for', removeForCartInputID + '-footable');
                removeForCartInput.attr('id', removeForCartInputID + '-footable');

                // for input[name=addtocart]
                $('label[for=' + addToCartInputID + ']').attr('for', addToCartInputID + '-footable');
                addToCartInput.attr('id', addToCartInputID + '-footable');

                // add a class to flag it as done
                rowDetail.addClass('checkboxIDChanged');

            }

        })

    }

    //function categoriesHoverEffect() {

    //    var grid = $('.home-page-category-grid')
    //    var items = $('.item-box', grid)

    //    items.on('hover', function () {
    //        $(this).addClass('hovered')
    //        items.each(function () {
    //            if (!$(this).hasClass('hovered')) {
    //                $(this).toggleClass('on')
    //            }
    //        })
    //        $(this).removeClass('hovered')
    //    })

    //}

    //function mobileBackButtonClose() {

    //   // use the back button on mobile to close navigations

    //    $('.overlayOffCanvas').on('click', function () {
    //        window.location.hash = window.location.hash.replace('opened', '');
    //    });

    //    $(document).on('onOverlayOffCanvasShow', function () {
    //        window.location.hash = 'opened' + window.location.hash;
    //    });

    //    $(window).on('hashchange', function () {
    //        if (window.location.hash.indexOf('opened') == -1) {
    //            $('.overlayOffCanvas').trigger('click');
    //        }
    //    });

    //}

    // OBJECTS

    var quickTabsSlider = {
        init: function () {
            var that = this;

            this.tabsWrap = $('.productTabs');
            this.controlsParent = $('.ui-tabs-nav');
            this.controls = $('.ui-tabs-nav li');
            this.listParent = $('.productTabs-body');
            this.listItems = $('.productTabs-body > div');

            //wrap the tabs list for the slider to work
            this.listParent.wrap('<div class="productTabs-body-wrap"></div>');

            //add classes for the active tab and its control
            this.listParent.children().first().addClass('visible');
            this.controlsParent.children().first().addClass('clicked');

            //activate onLoad the onResize functionality
            this.onResize();

            //onClick event for the slider dots (tab controls)
            this.controls.on('click.tab', function () {
                var thisIndex = $(this).index();

                if ($(that.listItems[thisIndex]).is(':empty') || $(that.listItems[thisIndex]).children().length < 1) {
                    $(window).one('quickTabsLoadedTab', function () {
                        that.tabControlClick(thisIndex);
                    });
                }
                else {
                    that.tabControlClick(thisIndex);
                }
            });

            //asures that the height is refreshed even when there are dynamically loaded elements in the tab
            this.tabsWrap.on('click', 'input[type=button]', function () {
                $(window).one('quickTabsRefreshedTab', function () {
                    that.listParent.css({
                        height: $(that.listParent).children('.visible').outerHeight()
                    });
                });
            });
        },
        tabControlClick: function (thisIndex) {
            var that = this;

            //custom classes adding for clicked/selected element
            that.controls.each(function () {
                $(this).removeClass('clicked');
            });
            $(that.listItems).each(function () {
                $(this).removeClass('visible');
            });
            $(this).addClass('clicked');
            $($(that.listItems)[thisIndex]).addClass('visible');

            //movement of the slider
            that.listParent.css({
                marginLeft: -(that.tabsWrap.width() * thisIndex),
                height: $(that.listItems[thisIndex]).outerHeight()
            });
        },
        onResize: function () {
            var that = this;
            this.tabsWrapWidth = this.tabsWrap.width();

            //refresh list items' width
            this.listItems.each(function () {
                $(this).css('width', that.tabsWrapWidth);
            });

            //refresh list's width and marginLeft values
            if ($('.productTabs-body > div.visible').length > 0) {
                this.listParent.css({
                    width: this.tabsWrapWidth * this.controls.length,
                    marginLeft: -(that.tabsWrap.width() * $(this.listParent).children('.visible').index()),
                    height: $(this.listParent).children('.visible').outerHeight()
                });
            }
        }
    };

})(jQuery, sevenSpikesCore, sevenSpikesEx);