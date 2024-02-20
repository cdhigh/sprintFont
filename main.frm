VERSION 5.00
Object = "{831FDD16-0C5C-11D2-A9FC-0000F8754DA1}#2.2#0"; "MSCOMCTL.OCX"
Begin VB.Form frmMain 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "sprintFont"
   ClientHeight    =   5370
   ClientLeft      =   45
   ClientTop       =   375
   ClientWidth     =   9360
   BeginProperty Font 
      Name            =   "΢���ź�"
      Size            =   10.5
      Charset         =   134
      Weight          =   400
      Underline       =   0   'False
      Italic          =   0   'False
      Strikethrough   =   0   'False
   EndProperty
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   5370
   ScaleWidth      =   9360
   ShowInTaskbar   =   0   'False
   StartUpPosition =   2  '��Ļ����
   Begin VB.Frame tabStrip__Tab6 
      Caption         =   "ArcTrack"
      Height          =   4695
      Left            =   4920
      TabIndex        =   74
      Top             =   5640
      Width           =   8895
      Begin VB.ComboBox cmbRoundedTrackSmallDistance 
         Height          =   420
         Left            =   2400
         TabIndex        =   87
         Text            =   "cmbhPercent"
         Top             =   2280
         Width           =   975
      End
      Begin VB.OptionButton optRoundedTrackBezier 
         Caption         =   "Bezier"
         Height          =   375
         Left            =   3720
         TabIndex        =   84
         Tag             =   "p@textvariable"
         Top             =   1080
         Width           =   1455
      End
      Begin VB.OptionButton optRoundedTrack3Points 
         Caption         =   "Three-point"
         Height          =   375
         Left            =   1800
         TabIndex        =   83
         Tag             =   "p@textvariable"
         Top             =   1080
         Width           =   1695
      End
      Begin VB.OptionButton optRoundedTrackTangent 
         Caption         =   "Tangent"
         Height          =   375
         Left            =   240
         TabIndex        =   82
         Tag             =   "p@textvariable"
         Top             =   1080
         Value           =   -1  'True
         Width           =   1335
      End
      Begin VB.ComboBox cmbRoundedTrackSegs 
         Height          =   420
         Left            =   2400
         TabIndex        =   79
         Text            =   "cmbSegs"
         Top             =   2880
         Width           =   975
      End
      Begin VB.CommandButton cmdRoundedTrackConvert 
         Caption         =   "Convert"
         Height          =   450
         Left            =   1200
         TabIndex        =   78
         Top             =   3840
         Width           =   2175
      End
      Begin VB.CommandButton cmdRoundedTrackCancel 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   77
         Top             =   3840
         Width           =   2175
      End
      Begin VB.ComboBox cmbRoundedTrackBigDistance 
         Height          =   420
         Left            =   2400
         TabIndex        =   76
         Text            =   "cmbhPercent"
         Top             =   1680
         Width           =   975
      End
      Begin VB.PictureBox picRoundedTrack 
         BorderStyle     =   0  'None
         Height          =   2415
         Left            =   5280
         ScaleHeight     =   2415
         ScaleWidth      =   3375
         TabIndex        =   75
         Top             =   960
         Width           =   3375
      End
      Begin VB.Label lblRoundedTrackSmallD 
         Alignment       =   1  'Right Justify
         Caption         =   "small d(mm)"
         Height          =   375
         Left            =   480
         TabIndex        =   88
         Top             =   2280
         Width           =   1815
      End
      Begin VB.Label lblSaveAsRoundedTrack 
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "΢���ź�"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7800
         TabIndex        =   86
         Top             =   3960
         Width           =   975
      End
      Begin VB.Label lblRoundedTrackBigD 
         Alignment       =   1  'Right Justify
         Caption         =   "big d(mm)"
         Height          =   375
         Left            =   480
         TabIndex        =   85
         Top             =   1680
         Width           =   1815
      End
      Begin VB.Label lblRoundedTrackSegs 
         Alignment       =   1  'Right Justify
         Caption         =   "segments"
         Height          =   375
         Left            =   480
         TabIndex        =   81
         Top             =   2880
         Width           =   1815
      End
      Begin VB.Label lblRoundedTrackTips 
         Alignment       =   2  'Center
         Caption         =   "rounded_track_features_tips"
         Height          =   495
         Left            =   240
         TabIndex        =   80
         Top             =   360
         Width           =   8415
      End
   End
   Begin VB.Frame tabStrip__Tab5 
      Caption         =   "Teardrop"
      Height          =   4695
      Left            =   3840
      TabIndex        =   61
      Top             =   5760
      Width           =   8895
      Begin VB.PictureBox picTeardrops 
         BorderStyle     =   0  'None
         Height          =   2415
         Left            =   4440
         ScaleHeight     =   2415
         ScaleWidth      =   3975
         TabIndex        =   73
         Top             =   960
         Width           =   3975
      End
      Begin VB.CheckBox chkIncludeSmdPads 
         Caption         =   "Include SMD pads"
         Height          =   375
         Left            =   1080
         TabIndex        =   72
         Tag             =   "p@textvariable"
         Top             =   3000
         Width           =   2775
      End
      Begin VB.CommandButton cmdRemoveTeardrops 
         Caption         =   "Remove"
         Height          =   450
         Left            =   2760
         TabIndex        =   70
         Top             =   3840
         Width           =   1815
      End
      Begin VB.ComboBox cmbhPercent 
         Height          =   420
         Left            =   2760
         TabIndex        =   66
         Text            =   "cmbhPercent"
         Top             =   1080
         Width           =   1215
      End
      Begin VB.CommandButton cmdCancelTeardrops 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   5160
         TabIndex        =   65
         Top             =   3840
         Width           =   1815
      End
      Begin VB.CommandButton cmdAddTeardrops 
         Caption         =   "Add"
         Height          =   450
         Left            =   360
         TabIndex        =   64
         Top             =   3840
         Width           =   1815
      End
      Begin VB.ComboBox cmbTeardropSegs 
         Height          =   420
         Left            =   2760
         TabIndex        =   63
         Text            =   "cmbSegs"
         Top             =   2280
         Width           =   1215
      End
      Begin VB.ComboBox cmbvPercent 
         Height          =   420
         Left            =   2760
         TabIndex        =   62
         Text            =   "cmbvPercent"
         Top             =   1680
         Width           =   1215
      End
      Begin VB.Label lblTeardropsTips 
         Alignment       =   2  'Center
         Caption         =   "teardrops_features_tips"
         Height          =   495
         Left            =   240
         TabIndex        =   71
         Top             =   360
         Width           =   8415
      End
      Begin VB.Label lblhPercent 
         Alignment       =   1  'Right Justify
         Caption         =   "Horizontal percent"
         Height          =   375
         Left            =   240
         TabIndex        =   69
         Top             =   1080
         Width           =   2295
      End
      Begin VB.Label lblTeardropSegs 
         Alignment       =   1  'Right Justify
         Caption         =   "Number of segments"
         Height          =   375
         Left            =   240
         TabIndex        =   68
         Top             =   2280
         Width           =   2295
      End
      Begin VB.Label lblvPercent 
         Alignment       =   1  'Right Justify
         Caption         =   "Vertical percent"
         Height          =   375
         Left            =   240
         TabIndex        =   67
         Top             =   1680
         Width           =   2295
      End
   End
   Begin VB.Frame tabStrip__Tab4 
      Caption         =   "AutoRouter"
      Height          =   4695
      Left            =   2760
      TabIndex        =   58
      Top             =   5760
      Width           =   8895
      Begin MSComctlLib.TreeView treRules 
         Height          =   1455
         Left            =   1560
         TabIndex        =   60
         Top             =   2160
         Width           =   6495
         _ExtentX        =   11456
         _ExtentY        =   2566
         _Version        =   393217
         Style           =   7
         Appearance      =   1
      End
      Begin VB.VScrollBar VSrlRules 
         Height          =   1455
         Left            =   8040
         TabIndex        =   54
         Top             =   2160
         Width           =   255
      End
      Begin VB.CommandButton cmdImportSes 
         Caption         =   "Import"
         Height          =   450
         Left            =   2760
         TabIndex        =   56
         Top             =   3840
         Width           =   1815
      End
      Begin VB.TextBox txtSesFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   51
         Top             =   1680
         Width           =   6495
      End
      Begin VB.CommandButton cmdSesFile 
         Caption         =   "..."
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   9
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   8160
         TabIndex        =   52
         Top             =   1680
         Width           =   495
      End
      Begin VB.CommandButton cmdCancelAutoRouter 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   5160
         TabIndex        =   57
         Top             =   3840
         Width           =   1815
      End
      Begin VB.CommandButton cmdExportDsn 
         Caption         =   "Export"
         Height          =   450
         Left            =   360
         TabIndex        =   55
         Top             =   3840
         Width           =   1815
      End
      Begin VB.TextBox txtDsnFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   48
         Top             =   1200
         Width           =   6495
      End
      Begin VB.CommandButton cmdDsnFile 
         Caption         =   "..."
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   9
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   8160
         TabIndex        =   49
         Top             =   1200
         Width           =   495
      End
      Begin VB.Label lblRules 
         Alignment       =   1  'Right Justify
         Caption         =   "Rules"
         Height          =   375
         Left            =   240
         TabIndex        =   53
         Top             =   2400
         Width           =   975
      End
      Begin VB.Label lblSesFile 
         Alignment       =   1  'Right Justify
         Caption         =   "Ses file"
         Height          =   375
         Left            =   240
         TabIndex        =   50
         Top             =   1680
         Width           =   975
      End
      Begin VB.Label lblSaveAsAutoRouter 
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "΢���ź�"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7800
         TabIndex        =   59
         Top             =   3960
         Width           =   975
      End
      Begin VB.Label lblAutoRouterTips 
         Caption         =   "AutoRouter_features_tips"
         Height          =   855
         Left            =   1560
         TabIndex        =   46
         Top             =   240
         Width           =   6855
      End
      Begin VB.Label lblDsnFile 
         Alignment       =   1  'Right Justify
         Caption         =   "Dsn file"
         Height          =   375
         Left            =   240
         TabIndex        =   47
         Top             =   1200
         Width           =   975
      End
   End
   Begin VB.Frame tabStrip__Tab3 
      Caption         =   "SVG"
      Height          =   4695
      Left            =   1920
      TabIndex        =   30
      Top             =   5760
      Width           =   8895
      Begin VB.ComboBox cmbSvgQrcode 
         Height          =   420
         Left            =   120
         Style           =   2  'Dropdown List
         TabIndex        =   45
         Tag             =   "p@justify='right'"
         Top             =   1500
         Width           =   1455
      End
      Begin VB.ComboBox cmbSvgMode 
         Height          =   420
         Left            =   1560
         Style           =   2  'Dropdown List
         TabIndex        =   40
         Top             =   2160
         Width           =   3135
      End
      Begin VB.ComboBox cmbSvgHeight 
         Height          =   420
         Left            =   6480
         TabIndex        =   39
         Top             =   2160
         Width           =   2175
      End
      Begin VB.ComboBox cmbSvgSmooth 
         Height          =   420
         Left            =   6480
         Style           =   2  'Dropdown List
         TabIndex        =   38
         Top             =   2760
         Width           =   2175
      End
      Begin VB.ComboBox cmbSvgLayer 
         Height          =   420
         Left            =   1560
         Style           =   2  'Dropdown List
         TabIndex        =   37
         Top             =   2760
         Width           =   3135
      End
      Begin VB.CommandButton cmdCancelSvg 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   34
         Top             =   3840
         Width           =   2175
      End
      Begin VB.CommandButton cmdOkSvg 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   33
         Top             =   3840
         Width           =   2175
      End
      Begin VB.TextBox txtSvgFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   32
         Top             =   1500
         Width           =   6495
      End
      Begin VB.CommandButton cmdSvgFile 
         Caption         =   "..."
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   9
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   8160
         TabIndex        =   31
         Top             =   1500
         Width           =   495
      End
      Begin VB.Label lblSvgHeight 
         Alignment       =   1  'Right Justify
         Caption         =   "Height (mm)"
         Height          =   375
         Left            =   4680
         TabIndex        =   44
         Top             =   2160
         Width           =   1695
      End
      Begin VB.Label lblSvgMode 
         Alignment       =   1  'Right Justify
         Caption         =   "Mode"
         Height          =   375
         Left            =   360
         TabIndex        =   43
         Top             =   2160
         Width           =   975
      End
      Begin VB.Label lblSvgSmooth 
         Alignment       =   1  'Right Justify
         Caption         =   "Smooth"
         Height          =   375
         Left            =   4680
         TabIndex        =   42
         Top             =   2760
         Width           =   1695
      End
      Begin VB.Label lblSvgLayer 
         Alignment       =   1  'Right Justify
         Caption         =   "Layer"
         Height          =   375
         Left            =   360
         TabIndex        =   41
         Top             =   2760
         Width           =   975
      End
      Begin VB.Label lblSaveAsSvg 
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "΢���ź�"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7800
         TabIndex        =   36
         Top             =   3960
         Width           =   975
      End
      Begin VB.Label lblSvgTips 
         Caption         =   "svg_features_tips"
         Height          =   975
         Left            =   1560
         TabIndex        =   35
         Top             =   360
         Width           =   6855
      End
   End
   Begin VB.Frame tabStrip__Tab2 
      Caption         =   "Footprint"
      Height          =   4695
      Left            =   840
      TabIndex        =   21
      Top             =   5760
      Width           =   8895
      Begin VB.CheckBox chkImportFootprintText 
         Caption         =   "Import text"
         Height          =   375
         Left            =   1560
         TabIndex        =   26
         Top             =   2880
         Value           =   1  'Checked
         Width           =   3015
      End
      Begin VB.CommandButton cmdFootprintFile 
         Caption         =   "..."
         BeginProperty Font 
            Name            =   "Arial"
            Size            =   9
            Charset         =   0
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   375
         Left            =   8160
         TabIndex        =   25
         Top             =   2160
         Width           =   495
      End
      Begin VB.TextBox txtFootprintFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   24
         Top             =   2160
         Width           =   6495
      End
      Begin VB.CommandButton cmdOkFootprint 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   27
         Top             =   3840
         Width           =   2175
      End
      Begin VB.CommandButton cmdCancelFootprint 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   28
         Top             =   3840
         Width           =   2175
      End
      Begin VB.Label lblFootprintFile 
         Alignment       =   1  'Right Justify
         Caption         =   "Input"
         Height          =   375
         Left            =   240
         TabIndex        =   23
         Top             =   2160
         Width           =   975
      End
      Begin VB.Label lblFootprintTips 
         Caption         =   "Footprint_features_tips"
         Height          =   1575
         Left            =   1560
         TabIndex        =   22
         Top             =   360
         Width           =   6855
      End
      Begin VB.Label lblSaveAsFootprint 
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "΢���ź�"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7800
         TabIndex        =   29
         Top             =   3960
         Width           =   975
      End
   End
   Begin MSComctlLib.TabStrip tabStrip 
      Height          =   4695
      Left            =   240
      TabIndex        =   1
      Top             =   240
      Width           =   8895
      _ExtentX        =   15690
      _ExtentY        =   8281
      _Version        =   393216
      BeginProperty Tabs {1EFB6598-857C-11D1-B16A-00C0F0283628} 
         NumTabs         =   1
         BeginProperty Tab1 {1EFB659A-857C-11D1-B16A-00C0F0283628} 
            ImageVarType    =   2
         EndProperty
      EndProperty
   End
   Begin MSComctlLib.StatusBar staBar 
      Align           =   2  'Align Bottom
      Height          =   345
      Left            =   0
      TabIndex        =   0
      Top             =   5025
      Width           =   9360
      _ExtentX        =   16510
      _ExtentY        =   609
      _Version        =   393216
      BeginProperty Panels {8E3867A5-8586-11D1-B16A-00C0F0283628} 
         NumPanels       =   1
         BeginProperty Panel1 {8E3867AB-8586-11D1-B16A-00C0F0283628} 
         EndProperty
      EndProperty
   End
   Begin VB.Frame tabStrip__Tab1 
      Caption         =   "Font"
      Height          =   4695
      Left            =   120
      TabIndex        =   2
      Top             =   5760
      Width           =   8895
      Begin VB.TextBox txtMain 
         BeginProperty Font 
            Name            =   "΢���ź�"
            Size            =   14.25
            Charset         =   134
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   855
         Left            =   1440
         MultiLine       =   -1  'True
         TabIndex        =   12
         Top             =   600
         Width           =   6735
      End
      Begin VB.ComboBox cmbLayer 
         Height          =   420
         Left            =   1440
         Style           =   2  'Dropdown List
         TabIndex        =   11
         Top             =   2400
         Width           =   3135
      End
      Begin VB.VScrollBar VScroll1 
         Height          =   855
         Left            =   8160
         TabIndex        =   10
         Top             =   600
         Width           =   255
      End
      Begin VB.ComboBox cmbSmooth 
         Height          =   420
         Left            =   1440
         Style           =   2  'Dropdown List
         TabIndex        =   9
         Top             =   3000
         Width           =   3135
      End
      Begin VB.CommandButton cmdOk 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   8
         Top             =   3840
         Width           =   2175
      End
      Begin VB.CommandButton cmdCancel 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   7
         Top             =   3840
         Width           =   2175
      End
      Begin VB.ComboBox cmbWordSpacing 
         Height          =   420
         Left            =   6960
         TabIndex        =   6
         Top             =   2400
         Width           =   1575
      End
      Begin VB.ComboBox cmbLineSpacing 
         Height          =   420
         Left            =   6960
         TabIndex        =   5
         Top             =   3000
         Width           =   1575
      End
      Begin VB.ComboBox cmbFontHeight 
         Height          =   420
         Left            =   6960
         TabIndex        =   4
         Top             =   1800
         Width           =   1575
      End
      Begin VB.ComboBox cmbFont 
         Height          =   420
         Left            =   1440
         Style           =   2  'Dropdown List
         TabIndex        =   3
         Top             =   1800
         Width           =   3135
      End
      Begin VB.Label lblTxt 
         Alignment       =   1  'Right Justify
         Caption         =   "Text"
         Height          =   375
         Left            =   240
         TabIndex        =   20
         Top             =   600
         Width           =   975
      End
      Begin VB.Label lblLayer 
         Alignment       =   1  'Right Justify
         Caption         =   "Layer"
         Height          =   375
         Left            =   240
         TabIndex        =   19
         Top             =   2400
         Width           =   975
      End
      Begin VB.Label lblSmooth 
         Alignment       =   1  'Right Justify
         Caption         =   "Smooth"
         Height          =   375
         Left            =   240
         TabIndex        =   18
         Top             =   3000
         Width           =   975
      End
      Begin VB.Label lblWordSpacing 
         Alignment       =   1  'Right Justify
         Caption         =   "Word spacing (mm)"
         Height          =   375
         Left            =   4680
         TabIndex        =   17
         Top             =   2400
         Width           =   2175
      End
      Begin VB.Label LblLineSpacing 
         Alignment       =   1  'Right Justify
         Caption         =   "Line spacing (mm)"
         Height          =   375
         Left            =   4680
         TabIndex        =   16
         Top             =   3000
         Width           =   2175
      End
      Begin VB.Label lblSaveAs 
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "΢���ź�"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7800
         TabIndex        =   15
         Top             =   3960
         Width           =   975
      End
      Begin VB.Label lblFont 
         Alignment       =   1  'Right Justify
         Caption         =   "Font"
         Height          =   375
         Left            =   240
         TabIndex        =   14
         Top             =   1800
         Width           =   975
      End
      Begin VB.Label lblFontHeight 
         Alignment       =   1  'Right Justify
         Caption         =   "Height (mm)"
         Height          =   375
         Left            =   4680
         TabIndex        =   13
         Top             =   1800
         Width           =   2175
      End
   End
End
Attribute VB_Name = "frmMain"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub cmbFont_Change()

End Sub

Private Sub lblSaveAs_Click()

End Sub

Private Sub lblSaveAsAutoRouter_Click()

End Sub

Private Sub lblSaveAsFootprint_Click()

End Sub

Private Sub lblSaveAsRoundedTrack_Click()

End Sub

Private Sub lblSaveAsSvg_Click()

End Sub

Private Sub tabStrip_Click()

End Sub

Private Sub treRules_DblClick()

End Sub
