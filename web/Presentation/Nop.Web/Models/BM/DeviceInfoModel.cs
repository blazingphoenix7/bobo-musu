using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Nop.Web.Models.BM
{
  public class DeviceInfoModel
  {
    public string Name { get; set; }
    public string Model { get; set; }
    public string OperatingSystem { get; set; }
    public string OsVersion { get; set; }
    public bool IsLoggedIn { get; set; }
    public DeviceType Type { get; set; }
  }

  public enum DeviceType
  {
    Web = 0,
    Android = 1,
    iOS = 2
  }
}
