from orti3dGui import *

class MySplash(wx.SplashScreen):
    def __init__(self):
        bmp = wx.Bitmap("utils/ipht3dSplash.gif",wx.BITMAP_TYPE_GIF)
        wx.SplashScreen.__init__(self, bmp,
                                wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT,
                                4000, None, -1,
                                style = wx.SIMPLE_BORDER|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP)

class orti3d(wx.App):

    def OnInit(self):
        wx.InitAllImageHandlers()
        #splash = MySplash()
        #splash.Show()
        fen = orti3dGui('Open Reactive Transport interface')
        fen.Show(True)
        self.SetTopWindow(fen)
        return True

app = orti3d(wx.Platform == "__WXMSW__")
app.MainLoop()
