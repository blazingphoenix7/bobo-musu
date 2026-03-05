using System;
using System.Collections.Generic;
using System.Text;

namespace Nop.Core.Common
{
  public struct PrintPath
  {
    public const string ROOT = "wwwroot/PrintFiles/{0}"; //{0} for Customer Id
    public const string ROOT_ORDER = "wwwroot/PrintOrders/{0}"; //{0} for Customer Id
    public const string ROOT_TEMP = "wwwroot/PrintTemps"; 
    public const string ROOT_MODEL_TEMPLATES = "wwwroot/PrintModelTemplates"; //{0} for Customer Id
    public const string RELATIVE = "/PrintFiles/{0}"; //{0} for Customer Id
    public const string RELATIVE_ORDER = "/PrintOrders/{0}"; //{0} for Customer Id
    public const string RELATIVE_TEMP = "/PrintTemps";
    public const string RELATIVE_MODEL_TEMPLATES = "/PrintModelTemplates"; //{0} for Customer Id
    public const string IMAGES = "Images";
    public const string MODELS = "Models";
    public const string THUMBS = "Thumbs";
  }

  public struct ViewDataKey
  {
    public const string IS_PRODUCT_DETAIL_PAGE = "IsProductDetailPage";
    public const string SHOW_GO_TO_TOP = "ShowGoToTop";
    public const string APPLY_BACK = "ApplyBack";
    public const string BACK_ICON_CLASS = "BackIconClass";
    public const string BACK_TEXT = "BackText";
    public const string BACK_ACTION = "BackAction";
    public const string SHOW_LEAVE_CONFIRMATION = "ShowLeaveConfirmation";
    public const string SHOW_FINGER_BACKGROUND = "ShowFingerBackground";
    public const string SHOW_SHOPPING_CART = "ShowShoppingCart";
  }
}
