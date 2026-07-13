VERSION 5.00
Object = "{831FDD16-0C5C-11D2-A9FC-0000F8754DA1}#2.2#0"; "MSCOMCTL.OCX"
Begin VB.Form frmMain 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "sprintFont"
   ClientHeight    =   6135
   ClientLeft      =   45
   ClientTop       =   375
   ClientWidth     =   10335
   BeginProperty Font 
      Name            =   "Î¢ÈíÑÅºÚ"
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
   ScaleHeight     =   6135
   ScaleWidth      =   10335
   ShowInTaskbar   =   0   'False
   StartUpPosition =   2  'ÆÁÄ»ÖÐÐÄ
   Begin VB.Frame tabStrip__Tab1 
      Caption         =   " Font "
      Height          =   5055
      Left            =   9360
      TabIndex        =   2
      Top             =   1800
      Width           =   9895
      Begin VB.CommandButton cmdLastText 
         Appearance      =   0  'Flat
         Caption         =   "¡î"
         Height          =   440
         Left            =   9360
         TabIndex        =   227
         TabStop         =   0   'False
         Top             =   775
         Width           =   375
      End
      Begin VB.CommandButton cmdSymbol 
         Appearance      =   0  'Flat
         Caption         =   "@"
         Height          =   440
         Left            =   9360
         TabIndex        =   226
         TabStop         =   0   'False
         Top             =   240
         Width           =   375
      End
      Begin VB.Frame frmInvertedBg 
         BackColor       =   &H00C0C0C0&
         Height          =   1335
         Left            =   0
         TabIndex        =   87
         Top             =   3000
         Width           =   9975
         Begin VB.CheckBox chkInvertedBackground 
            BackColor       =   &H00C0C0C0&
            Caption         =   "Inverted Background"
            BeginProperty Font 
               Name            =   "Î¢ÈíÑÅºÚ"
               Size            =   10.5
               Charset         =   134
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            ForeColor       =   &H00000000&
            Height          =   375
            Left            =   1440
            TabIndex        =   91
            Top             =   120
            Width           =   3495
         End
         Begin VB.ComboBox cmbPadding 
            BackColor       =   &H00808080&
            Height          =   420
            Left            =   1560
            TabIndex        =   90
            Top             =   720
            Width           =   3015
         End
         Begin VB.ComboBox cmbCapLeft 
            BackColor       =   &H00808080&
            BeginProperty Font 
               Name            =   "Times New Roman"
               Size            =   12
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   405
            Left            =   8040
            Style           =   2  'Dropdown List
            TabIndex        =   89
            Top             =   120
            Width           =   1575
         End
         Begin VB.ComboBox cmbCapRight 
            BackColor       =   &H00808080&
            BeginProperty Font 
               Name            =   "Times New Roman"
               Size            =   12
               Charset         =   0
               Weight          =   700
               Underline       =   0   'False
               Italic          =   0   'False
               Strikethrough   =   0   'False
            EndProperty
            Height          =   405
            Left            =   8040
            Style           =   2  'Dropdown List
            TabIndex        =   88
            Top             =   720
            Width           =   1575
         End
         Begin VB.Label lblBkPadding 
            Alignment       =   1  'Right Justify
            BackColor       =   &H00C0C0C0&
            Caption         =   "Padding"
            ForeColor       =   &H00000000&
            Height          =   375
            Left            =   240
            TabIndex        =   94
            Top             =   720
            Width           =   1215
         End
         Begin VB.Label lblCapLeft 
            Alignment       =   1  'Right Justify
            BackColor       =   &H00C0C0C0&
            Caption         =   "Cap left"
            ForeColor       =   &H00000000&
            Height          =   375
            Left            =   5280
            TabIndex        =   93
            Top             =   120
            Width           =   2655
         End
         Begin VB.Label lblCapRight 
            Alignment       =   1  'Right Justify
            BackColor       =   &H00C0C0C0&
            Caption         =   "Cap right"
            ForeColor       =   &H00000000&
            Height          =   375
            Left            =   5280
            TabIndex        =   92
            Top             =   720
            Width           =   2655
         End
      End
      Begin VB.TextBox txtMain 
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   14.25
            Charset         =   134
            Weight          =   400
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         Height          =   975
         Left            =   1560
         MultiLine       =   -1  'True
         TabIndex        =   12
         Top             =   240
         Width           =   7425
      End
      Begin VB.ComboBox cmbLayer 
         Height          =   420
         ItemData        =   "main.frx":0000
         Left            =   1560
         List            =   "main.frx":0002
         Style           =   2  'Dropdown List
         TabIndex        =   11
         Top             =   1920
         Width           =   3015
      End
      Begin VB.VScrollBar VScroll1 
         Height          =   975
         Left            =   9000
         TabIndex        =   10
         Top             =   240
         Width           =   255
      End
      Begin VB.ComboBox cmbSmooth 
         Height          =   420
         Left            =   1560
         Style           =   2  'Dropdown List
         TabIndex        =   9
         Top             =   2520
         Width           =   3015
      End
      Begin VB.CommandButton cmdOk 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   8
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdCancel 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   7
         Top             =   4440
         Width           =   2175
      End
      Begin VB.ComboBox cmbWordSpacing 
         Height          =   420
         Left            =   8040
         TabIndex        =   6
         Top             =   1920
         Width           =   1575
      End
      Begin VB.ComboBox cmbLineSpacing 
         Height          =   420
         Left            =   8040
         TabIndex        =   5
         Top             =   2520
         Width           =   1575
      End
      Begin VB.ComboBox cmbFontHeight 
         Height          =   420
         Left            =   8040
         TabIndex        =   4
         Top             =   1320
         Width           =   1575
      End
      Begin VB.ComboBox cmbFont 
         Height          =   420
         Left            =   1560
         Style           =   2  'Dropdown List
         TabIndex        =   3
         Top             =   1320
         Width           =   3015
      End
      Begin VB.Label lblTxt 
         Alignment       =   1  'Right Justify
         Caption         =   "Text"
         Height          =   375
         Left            =   480
         TabIndex        =   20
         Top             =   240
         Width           =   975
      End
      Begin VB.Label lblLayer 
         Alignment       =   1  'Right Justify
         Caption         =   "Layer"
         Height          =   375
         Left            =   240
         TabIndex        =   19
         Top             =   1920
         Width           =   1215
      End
      Begin VB.Label lblSmooth 
         Alignment       =   1  'Right Justify
         Caption         =   "Smooth"
         Height          =   375
         Left            =   240
         TabIndex        =   18
         Top             =   2520
         Width           =   1215
      End
      Begin VB.Label lblWordSpacing 
         Alignment       =   1  'Right Justify
         Caption         =   "Word spacing (mm)"
         Height          =   375
         Left            =   5040
         TabIndex        =   17
         Top             =   1920
         Width           =   2895
      End
      Begin VB.Label LblLineSpacing 
         Alignment       =   1  'Right Justify
         Caption         =   "Line spacing (mm)"
         Height          =   375
         Left            =   5040
         TabIndex        =   16
         Top             =   2520
         Width           =   2895
      End
      Begin VB.Label lblSaveAs 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   6960
         TabIndex        =   15
         Top             =   4560
         Width           =   1815
      End
      Begin VB.Label lblFont 
         Alignment       =   1  'Right Justify
         Caption         =   "Font"
         Height          =   375
         Left            =   240
         TabIndex        =   14
         Top             =   1320
         Width           =   1215
      End
      Begin VB.Label lblFontHeight 
         Alignment       =   1  'Right Justify
         Caption         =   "Height (mm)"
         Height          =   375
         Left            =   5040
         TabIndex        =   13
         Top             =   1320
         Width           =   2895
      End
   End
   Begin VB.Frame tabStrip__Tab2 
      Caption         =   " Footprint "
      Height          =   5055
      Left            =   11760
      TabIndex        =   21
      Top             =   240
      Width           =   9895
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
         Left            =   9000
         TabIndex        =   25
         Top             =   2160
         Width           =   495
      End
      Begin VB.TextBox txtFootprintFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   24
         Top             =   2160
         Width           =   7335
      End
      Begin VB.CommandButton cmdOkFootprint 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   27
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdCancelFootprint 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   28
         Top             =   4440
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
         Caption         =   "Currently supports:\n1. Kicad footprint Library : *.kicad_mod\n2. EasyEDA part ID: C + number (C can be omitted)"
         Height          =   1575
         Left            =   1560
         TabIndex        =   22
         Top             =   360
         Width           =   7815
      End
      Begin VB.Label lblSaveAsFootprint 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   6960
         TabIndex        =   29
         Top             =   4560
         Width           =   1695
      End
   End
   Begin VB.Frame tabStrip__Tab9 
      Caption         =   " BulkEdit "
      Height          =   5055
      Left            =   9480
      TabIndex        =   126
      Top             =   3840
      Width           =   9895
      Begin VB.Frame frmBulkEditTrack 
         Height          =   3015
         Left            =   120
         TabIndex        =   163
         Top             =   1440
         Width           =   9615
         Begin VB.CheckBox chkBulkTrackLayerIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   172
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkTrackLayerIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   171
            Top             =   120
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTrackLayerThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   170
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkTrackLayerThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   169
            Top             =   120
            Width           =   2415
         End
         Begin VB.TextBox txtBulkTrackWidthIfValue 
            Height          =   420
            Left            =   4080
            TabIndex        =   168
            Text            =   "0.3"
            Top             =   720
            Width           =   855
         End
         Begin VB.ComboBox cmbBulkTrackWidthIfOp 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   167
            Top             =   720
            Width           =   1335
         End
         Begin VB.CheckBox chkBulkTrackWidthIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   166
            TabStop         =   0   'False
            Top             =   720
            Width           =   320
         End
         Begin VB.TextBox txtBulkTrackWidthThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   165
            Text            =   "0.3"
            Top             =   720
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTrackWidthThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   164
            TabStop         =   0   'False
            Top             =   720
            Width           =   320
         End
         Begin VB.Label lblBulkTrackLayer 
            Caption         =   "Layer"
            Height          =   375
            Left            =   120
            TabIndex        =   174
            Top             =   120
            Width           =   1815
         End
         Begin VB.Line Line3 
            BorderColor     =   &H00808080&
            X1              =   5640
            X2              =   5640
            Y1              =   120
            Y2              =   1100
         End
         Begin VB.Label lblBulkTrackWidth 
            Caption         =   "Width"
            Height          =   375
            Left            =   120
            TabIndex        =   173
            Top             =   720
            Width           =   1815
         End
      End
      Begin VB.Frame frmBulkEditText 
         Height          =   3015
         Left            =   120
         TabIndex        =   132
         Top             =   1440
         Width           =   9615
         Begin VB.TextBox txtBulkTextRotationThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   158
            Text            =   "0"
            Top             =   2400
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTextRotationThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   157
            TabStop         =   0   'False
            Top             =   2400
            Width           =   320
         End
         Begin VB.TextBox txtBulkTextRotationIf 
            Height          =   420
            Left            =   2520
            TabIndex        =   155
            Text            =   "0"
            Top             =   2400
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTextRotationIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   154
            TabStop         =   0   'False
            Top             =   2400
            Width           =   320
         End
         Begin VB.CheckBox chkBulkTextStyleThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   153
            TabStop         =   0   'False
            Top             =   1830
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkTextStyleThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   152
            Top             =   1830
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTextThicknessThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   151
            TabStop         =   0   'False
            Top             =   1260
            Width           =   320
         End
         Begin VB.CheckBox chkBulkTextHeightThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   150
            TabStop         =   0   'False
            Top             =   690
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkTextLayerThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   149
            Top             =   120
            Width           =   2415
         End
         Begin VB.ComboBox cmbBulkTextThicknessThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   148
            Top             =   1260
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTextLayerThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   147
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.TextBox txtBulkTextHeightThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   146
            Text            =   "1.0"
            Top             =   690
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTextStyleIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   141
            TabStop         =   0   'False
            Top             =   1830
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkTextStyleIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   140
            Top             =   1830
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkTextThicknessIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   139
            TabStop         =   0   'False
            Top             =   1260
            Width           =   320
         End
         Begin VB.CheckBox chkBulkTextHeightIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   138
            TabStop         =   0   'False
            Top             =   690
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkTextLayerIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   137
            Top             =   120
            Width           =   2415
         End
         Begin VB.ComboBox cmbBulkTextThicknessIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   136
            Top             =   1260
            Width           =   2415
         End
         Begin VB.ComboBox cmbBulkTextHeightIfOp 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   135
            Top             =   690
            Width           =   1335
         End
         Begin VB.CheckBox chkBulkTextLayerIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   134
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.TextBox txtBulkTextHeightIfValue 
            Height          =   420
            Left            =   4080
            TabIndex        =   133
            Text            =   "1.0"
            Top             =   690
            Width           =   855
         End
         Begin VB.Line Line2 
            BorderColor     =   &H00808080&
            X1              =   5640
            X2              =   5640
            Y1              =   120
            Y2              =   2760
         End
         Begin VB.Label lblBulkTextRotaion 
            Caption         =   "Rotation"
            Height          =   375
            Left            =   120
            TabIndex        =   156
            Top             =   2400
            Width           =   1815
         End
         Begin VB.Label lblBulkTextStyle 
            Caption         =   "Style"
            Height          =   375
            Left            =   120
            TabIndex        =   145
            Top             =   1830
            Width           =   1815
         End
         Begin VB.Label lblBulkTextThickness 
            Caption         =   "Thickness"
            Height          =   375
            Left            =   120
            TabIndex        =   144
            Top             =   1260
            Width           =   1815
         End
         Begin VB.Label lblBulkTextHeight 
            Caption         =   "Height"
            Height          =   375
            Left            =   120
            TabIndex        =   143
            Top             =   690
            Width           =   1815
         End
         Begin VB.Label lblBulkTextLayer 
            Caption         =   "Layer"
            Height          =   375
            Left            =   120
            TabIndex        =   142
            Top             =   120
            Width           =   1815
         End
      End
      Begin VB.Frame frmBulkEditPad 
         Height          =   3015
         Left            =   120
         TabIndex        =   175
         Top             =   1440
         Width           =   9615
         Begin VB.TextBox txtBulkPadDrillThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   202
            Text            =   "0.8"
            Top             =   1200
            Width           =   2415
         End
         Begin VB.TextBox txtBulkPadDrillIfValue 
            Height          =   420
            Left            =   4080
            TabIndex        =   201
            Text            =   "0.8"
            Top             =   1200
            Width           =   855
         End
         Begin VB.TextBox txtBulkPadSizeIfValue 
            Height          =   420
            Left            =   4080
            TabIndex        =   195
            Text            =   "1.5"
            Top             =   690
            Width           =   855
         End
         Begin VB.CheckBox chkBulkPadLayerIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   194
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkPadSizeIfOp 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   193
            Top             =   690
            Width           =   1335
         End
         Begin VB.ComboBox cmbBulkPadDrillIfOp 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   192
            Top             =   1260
            Width           =   1335
         End
         Begin VB.ComboBox cmbBulkPadLayerIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   191
            Top             =   120
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkPadSizeIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   190
            TabStop         =   0   'False
            Top             =   690
            Width           =   320
         End
         Begin VB.CheckBox chkBulkPadDrillIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   189
            TabStop         =   0   'False
            Top             =   1260
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkPadFormIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   188
            Top             =   1830
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkPadFormIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   187
            TabStop         =   0   'False
            Top             =   1830
            Width           =   320
         End
         Begin VB.TextBox txtBulkPadSizeThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   186
            Text            =   "1.5"
            Top             =   690
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkPadLayerThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   185
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkPadLayerThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   184
            Top             =   120
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkPadSizeThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   183
            TabStop         =   0   'False
            Top             =   690
            Width           =   320
         End
         Begin VB.CheckBox chkBulkPadDrillThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   182
            TabStop         =   0   'False
            Top             =   1260
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkPadFormThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   181
            Top             =   1830
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkPadFormThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   180
            TabStop         =   0   'False
            Top             =   1830
            Width           =   320
         End
         Begin VB.CheckBox chkBulkPadRotationIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   179
            TabStop         =   0   'False
            Top             =   2400
            Width           =   320
         End
         Begin VB.TextBox txtBulkPadRotationIf 
            Height          =   420
            Left            =   2520
            TabIndex        =   178
            Text            =   "0"
            Top             =   2400
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkPadRotationThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   177
            TabStop         =   0   'False
            Top             =   2400
            Width           =   320
         End
         Begin VB.TextBox txtBulkPadRotationThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   176
            Text            =   "0"
            Top             =   2400
            Width           =   2415
         End
         Begin VB.Label lblBulkPadLayer 
            Caption         =   "Layer"
            Height          =   375
            Left            =   120
            TabIndex        =   200
            Top             =   120
            Width           =   1815
         End
         Begin VB.Label lblBulkPadSize 
            Caption         =   "Size"
            Height          =   375
            Left            =   120
            TabIndex        =   199
            Top             =   690
            Width           =   1815
         End
         Begin VB.Label lblBulkPadDrill 
            Caption         =   "Drill"
            Height          =   375
            Left            =   120
            TabIndex        =   198
            Top             =   1260
            Width           =   1815
         End
         Begin VB.Label lblBulkPadForm 
            Caption         =   "Form"
            Height          =   375
            Left            =   120
            TabIndex        =   197
            Top             =   1830
            Width           =   1815
         End
         Begin VB.Label lblBulkPadRotation 
            Caption         =   "Rotation"
            Height          =   375
            Left            =   120
            TabIndex        =   196
            Top             =   2400
            Width           =   1815
         End
         Begin VB.Line Line4 
            BorderColor     =   &H00808080&
            X1              =   5640
            X2              =   5640
            Y1              =   120
            Y2              =   2760
         End
      End
      Begin VB.Frame frmBulkEditSmdPad 
         Height          =   3015
         Left            =   120
         TabIndex        =   203
         Top             =   1440
         Width           =   9615
         Begin VB.TextBox txtBulkSmdPadRotationThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   221
            Text            =   "0"
            Top             =   1800
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkSmdPadRotationThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   220
            TabStop         =   0   'False
            Top             =   1800
            Width           =   320
         End
         Begin VB.TextBox txtBulkSmdPadRotationIf 
            Height          =   420
            Left            =   2520
            TabIndex        =   219
            Text            =   "0"
            Top             =   1800
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkSmdPadRotationIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   218
            TabStop         =   0   'False
            Top             =   1800
            Width           =   320
         End
         Begin VB.CheckBox chkBulkSmdPadSizeYThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   217
            TabStop         =   0   'False
            Top             =   1240
            Width           =   320
         End
         Begin VB.CheckBox chkBulkSmdPadSizeXThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   216
            TabStop         =   0   'False
            Top             =   680
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkSmdPadLayerThen 
            Height          =   420
            Left            =   7080
            Style           =   2  'Dropdown List
            TabIndex        =   215
            Top             =   120
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkSmdPadLayerThen 
            Height          =   375
            Left            =   6720
            TabIndex        =   214
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.TextBox txtBulkSmdPadSizeXThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   213
            Text            =   "1.5"
            Top             =   680
            Width           =   2415
         End
         Begin VB.CheckBox chkBulkSmdPadSizeYIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   212
            TabStop         =   0   'False
            Top             =   1240
            Width           =   320
         End
         Begin VB.CheckBox chkBulkSmdPadSizeXIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   211
            TabStop         =   0   'False
            Top             =   680
            Width           =   320
         End
         Begin VB.ComboBox cmbBulkSmdPadLayerIf 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   210
            Top             =   120
            Width           =   2415
         End
         Begin VB.ComboBox cmbBulkSmdPadSizeYIfOp 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   209
            Top             =   1240
            Width           =   1335
         End
         Begin VB.ComboBox cmbBulkSmdPadSizeXIfOp 
            Height          =   420
            Left            =   2520
            Style           =   2  'Dropdown List
            TabIndex        =   208
            Top             =   680
            Width           =   1335
         End
         Begin VB.CheckBox chkBulkSmdPadLayerIf 
            Height          =   375
            Left            =   2160
            TabIndex        =   207
            TabStop         =   0   'False
            Top             =   120
            Width           =   320
         End
         Begin VB.TextBox txtBulkSmdPadSizeXIfValue 
            Height          =   420
            Left            =   4080
            TabIndex        =   206
            Text            =   "1.5"
            Top             =   680
            Width           =   855
         End
         Begin VB.TextBox txtBulkSmdPadSizeYIfValue 
            Height          =   420
            Left            =   4080
            TabIndex        =   205
            Text            =   "0.8"
            Top             =   1240
            Width           =   855
         End
         Begin VB.TextBox txtBulkSmdPadSizeYThen 
            Height          =   420
            Left            =   7080
            TabIndex        =   204
            Text            =   "0.8"
            Top             =   1240
            Width           =   2415
         End
         Begin VB.Line Line5 
            BorderColor     =   &H00808080&
            X1              =   5640
            X2              =   5640
            Y1              =   120
            Y2              =   2280
         End
         Begin VB.Label lblBulkSmdPadRotation 
            Caption         =   "Rotation"
            Height          =   375
            Left            =   120
            TabIndex        =   225
            Top             =   1800
            Width           =   1815
         End
         Begin VB.Label lblBulkSmdPadSizeY 
            Caption         =   "Size Y"
            Height          =   375
            Left            =   120
            TabIndex        =   224
            Top             =   1240
            Width           =   1815
         End
         Begin VB.Label lblBulkSmdPadSizeX 
            Caption         =   "Size X"
            Height          =   375
            Left            =   120
            TabIndex        =   223
            Top             =   680
            Width           =   1815
         End
         Begin VB.Label lblBulkSmdPadLayer 
            Caption         =   "Layer"
            Height          =   375
            Left            =   120
            TabIndex        =   222
            Top             =   120
            Width           =   1815
         End
      End
      Begin VB.CheckBox chkBulkEditApplyToAll 
         Caption         =   "Apply to all items (Ignore conditions)"
         Height          =   375
         Left            =   4800
         TabIndex        =   162
         Top             =   240
         Width           =   4935
      End
      Begin VB.CommandButton cmdCancelBulkEdit 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   129
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdBulkEditOk 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   128
         Top             =   4440
         Width           =   2175
      End
      Begin VB.ComboBox cmbBulkEditTarget 
         Height          =   420
         Left            =   1920
         Style           =   2  'Dropdown List
         TabIndex        =   127
         Top             =   240
         Width           =   1575
      End
      Begin VB.Line Line1 
         BorderColor     =   &H00808080&
         X1              =   240
         X2              =   9360
         Y1              =   1320
         Y2              =   1320
      End
      Begin VB.Label lblBulkEditThen 
         Caption         =   "Override (Then)"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   11.25
            Charset         =   134
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00808080&
         Height          =   375
         Left            =   6840
         TabIndex        =   161
         Top             =   840
         Width           =   2775
      End
      Begin VB.Label lblBulkEditIf 
         Caption         =   "Condition (If)"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   11.25
            Charset         =   134
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00808080&
         Height          =   375
         Left            =   2280
         TabIndex        =   160
         Top             =   840
         Width           =   2895
      End
      Begin VB.Label lblBulkEditProperty 
         Caption         =   "Property"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   11.25
            Charset         =   134
            Weight          =   700
            Underline       =   0   'False
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00808080&
         Height          =   375
         Left            =   240
         TabIndex        =   159
         Top             =   840
         Width           =   1335
      End
      Begin VB.Label lblBulkEditSaveAs 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   6960
         TabIndex        =   131
         Top             =   4560
         Width           =   1695
      End
      Begin VB.Label lblBulkEditTarget 
         Alignment       =   1  'Right Justify
         Caption         =   "Target"
         Height          =   375
         Left            =   240
         TabIndex        =   130
         Top             =   240
         Width           =   1455
      End
   End
   Begin VB.Frame tabStrip__Tab7 
      Caption         =   " RoundedTrack "
      Height          =   5055
      Left            =   10320
      TabIndex        =   73
      Top             =   1200
      Width           =   9895
      Begin VB.CheckBox chkMergeConnectedTracks 
         Caption         =   "Merge Connected Tracks"
         Height          =   375
         Left            =   840
         TabIndex        =   124
         Top             =   3600
         Width           =   4095
      End
      Begin VB.ComboBox cmbRoundedTrackType 
         Height          =   420
         Left            =   3000
         Style           =   2  'Dropdown List
         TabIndex        =   95
         Top             =   1080
         Width           =   1935
      End
      Begin VB.ComboBox cmbRoundedTrackSmallDistance 
         Height          =   420
         Left            =   3000
         TabIndex        =   83
         Text            =   "cmbhPercent"
         Top             =   2280
         Width           =   1935
      End
      Begin VB.ComboBox cmbRoundedTrackSegs 
         Height          =   420
         Left            =   3000
         TabIndex        =   78
         Text            =   "cmbSegs"
         Top             =   2880
         Width           =   1935
      End
      Begin VB.CommandButton cmdRoundedTrackConvert 
         Caption         =   "Convert"
         Height          =   450
         Left            =   1200
         TabIndex        =   77
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdRoundedTrackCancel 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   76
         Top             =   4440
         Width           =   2175
      End
      Begin VB.ComboBox cmbRoundedTrackBigDistance 
         Height          =   420
         Left            =   3000
         TabIndex        =   75
         Text            =   "cmbhPercent"
         Top             =   1680
         Width           =   1935
      End
      Begin VB.PictureBox picRoundedTrack 
         BorderStyle     =   0  'None
         Height          =   2415
         Left            =   5520
         ScaleHeight     =   2415
         ScaleWidth      =   3375
         TabIndex        =   74
         Top             =   1080
         Width           =   3375
      End
      Begin VB.Label lblRoundedTrackType 
         Alignment       =   1  'Right Justify
         Caption         =   "Type"
         Height          =   375
         Left            =   480
         TabIndex        =   96
         Top             =   1080
         Width           =   2415
      End
      Begin VB.Label lblRoundedTrackSmallD 
         Alignment       =   1  'Right Justify
         Caption         =   "small d(mm)"
         Height          =   375
         Left            =   480
         TabIndex        =   84
         Top             =   2280
         Width           =   2415
      End
      Begin VB.Label lblSaveAsRoundedTrack 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   6960
         TabIndex        =   82
         Top             =   4560
         Width           =   1695
      End
      Begin VB.Label lblRoundedTrackBigD 
         Alignment       =   1  'Right Justify
         Caption         =   "big d(mm)"
         Height          =   375
         Left            =   480
         TabIndex        =   81
         Top             =   1680
         Width           =   2415
      End
      Begin VB.Label lblRoundedTrackSegs 
         Alignment       =   1  'Right Justify
         Caption         =   "Number of segments"
         Height          =   375
         Left            =   480
         TabIndex        =   80
         Top             =   2880
         Width           =   2415
      End
      Begin VB.Label lblRoundedTrackTips 
         Alignment       =   2  'Center
         Caption         =   "Apply to all tracks when deselecting all, otherwise apply to selected tracks only"
         Height          =   495
         Left            =   240
         TabIndex        =   79
         Top             =   360
         Width           =   9375
      End
   End
   Begin VB.Frame tabStrip__Tab3 
      Caption         =   " Export "
      Height          =   5055
      Left            =   9840
      TabIndex        =   114
      Top             =   2640
      Width           =   9895
      Begin VB.CheckBox chkLayeredScad 
         Caption         =   "Export as Layered OpenSCAD"
         Height          =   375
         Left            =   960
         TabIndex        =   125
         Top             =   3360
         Width           =   3615
      End
      Begin VB.ComboBox cmbExportLayer 
         Height          =   420
         ItemData        =   "main.frx":0004
         Left            =   1560
         List            =   "main.frx":0006
         Style           =   2  'Dropdown List
         TabIndex        =   122
         Top             =   2760
         Width           =   3015
      End
      Begin VB.CommandButton cmdCancelExport 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   118
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdExport 
         Caption         =   "Export"
         Height          =   450
         Left            =   1200
         TabIndex        =   117
         Top             =   4440
         Width           =   2175
      End
      Begin VB.TextBox txtExportFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   116
         Top             =   2040
         Width           =   7335
      End
      Begin VB.CommandButton cmdChooseExportFile 
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
         Left            =   9000
         TabIndex        =   115
         Top             =   2040
         Width           =   495
      End
      Begin VB.Label lblExportLayerTips 
         Caption         =   "Only for OpenSCAD and SVG"
         Height          =   375
         Left            =   4680
         TabIndex        =   123
         Top             =   2760
         Width           =   4815
      End
      Begin VB.Label lblExportLayer 
         Alignment       =   1  'Right Justify
         Caption         =   "Layer"
         Height          =   375
         Left            =   240
         TabIndex        =   121
         Top             =   2760
         Width           =   1215
      End
      Begin VB.Label lblExportTips 
         Caption         =   "Currently supports:\n1. Kicad PCB file : *.kicad_pcb\n2. OpenSCAD file : *.scad\n3. SVG file : *.svg"
         Height          =   1335
         Left            =   1560
         TabIndex        =   120
         Top             =   360
         Width           =   7815
      End
      Begin VB.Label lblExportFile 
         Alignment       =   1  'Right Justify
         Caption         =   "Output"
         Height          =   375
         Left            =   240
         TabIndex        =   119
         Top             =   2040
         Width           =   1215
      End
   End
   Begin VB.Frame tabStrip__Tab5 
      Caption         =   " AutoRouter "
      Height          =   5055
      Left            =   8640
      TabIndex        =   58
      Top             =   6000
      Width           =   9895
      Begin MSComctlLib.TreeView treRules 
         Height          =   1815
         Left            =   1800
         TabIndex        =   60
         Top             =   2160
         Width           =   7575
         _ExtentX        =   13361
         _ExtentY        =   3201
         _Version        =   393217
         Style           =   7
         Appearance      =   1
      End
      Begin VB.VScrollBar VSrlRules 
         Height          =   1815
         Left            =   9360
         TabIndex        =   54
         Top             =   2160
         Width           =   255
      End
      Begin VB.CommandButton cmdImportSes 
         Caption         =   "Import SES"
         Height          =   450
         Left            =   2760
         TabIndex        =   56
         Top             =   4440
         Width           =   1815
      End
      Begin VB.TextBox txtSesFile 
         Height          =   420
         Left            =   1800
         TabIndex        =   51
         Top             =   1680
         Width           =   7215
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
         Left            =   9120
         TabIndex        =   52
         Top             =   1680
         Width           =   495
      End
      Begin VB.CommandButton cmdCancelAutoRouter 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   5160
         TabIndex        =   57
         Top             =   4440
         Width           =   1815
      End
      Begin VB.CommandButton cmdExportDsn 
         Caption         =   "Export DSN"
         Height          =   450
         Left            =   360
         TabIndex        =   55
         Top             =   4440
         Width           =   1815
      End
      Begin VB.TextBox txtDsnFile 
         Height          =   420
         Left            =   1800
         TabIndex        =   48
         Top             =   1200
         Width           =   7215
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
         Left            =   9120
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
         Width           =   1455
      End
      Begin VB.Label lblSesFile 
         Alignment       =   1  'Right Justify
         Caption         =   "Ses file"
         Height          =   375
         Left            =   240
         TabIndex        =   50
         Top             =   1680
         Width           =   1455
      End
      Begin VB.Label lblSaveAsAutoRouter 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7200
         TabIndex        =   59
         Top             =   4560
         Width           =   1455
      End
      Begin VB.Label lblAutoRouterTips 
         Caption         =   "Open the exported DSN file with Freerouting for autorouting\nCurrently only supports all components placed on the front side"
         Height          =   855
         Left            =   1560
         TabIndex        =   46
         Top             =   240
         Width           =   7935
      End
      Begin VB.Label lblDsnFile 
         Alignment       =   1  'Right Justify
         Caption         =   "Dsn file"
         Height          =   375
         Left            =   240
         TabIndex        =   47
         Top             =   1200
         Width           =   1455
      End
   End
   Begin VB.Frame tabStrip__Tab8 
      Caption         =   " WirePair "
      Height          =   5055
      Left            =   8160
      TabIndex        =   97
      Top             =   6480
      Width           =   9895
      Begin VB.TextBox txtWirePairSkew 
         Height          =   420
         Left            =   3240
         TabIndex        =   112
         Text            =   "0.0"
         Top             =   3360
         Width           =   1935
      End
      Begin VB.CommandButton cmdOpenWirePairTuner 
         Caption         =   "Adjust"
         Height          =   450
         Left            =   120
         TabIndex        =   111
         Top             =   4440
         Width           =   2175
      End
      Begin VB.TextBox txtWirePairSpacing 
         Height          =   420
         Left            =   3240
         TabIndex        =   110
         Text            =   "0.6"
         Top             =   2880
         Width           =   1935
      End
      Begin VB.TextBox txtWirePairAmax 
         Height          =   420
         Left            =   3240
         TabIndex        =   108
         Text            =   "1"
         Top             =   2400
         Width           =   1935
      End
      Begin VB.TextBox txtWirePairAmin 
         Height          =   420
         Left            =   3240
         TabIndex        =   107
         Text            =   "0.1"
         Top             =   1920
         Width           =   1935
      End
      Begin VB.PictureBox picWirePair 
         BorderStyle     =   0  'None
         Height          =   2655
         Left            =   5520
         ScaleHeight     =   2655
         ScaleWidth      =   3615
         TabIndex        =   101
         Top             =   1200
         Width           =   3615
      End
      Begin VB.CommandButton cmdCancelWirePair 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   5400
         TabIndex        =   100
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdOkWirePair 
         Caption         =   "Ok"
         Height          =   450
         Left            =   2760
         TabIndex        =   99
         Top             =   4440
         Width           =   2175
      End
      Begin VB.ComboBox cmbWirePairType 
         Height          =   420
         Left            =   3240
         Style           =   2  'Dropdown List
         TabIndex        =   98
         Top             =   1440
         Width           =   1935
      End
      Begin VB.Label lblTargetSkew 
         Alignment       =   1  'Right Justify
         Caption         =   "Target skew"
         Height          =   375
         Left            =   120
         TabIndex        =   113
         Top             =   3360
         Width           =   3015
      End
      Begin VB.Label lblSpacing 
         Alignment       =   1  'Right Justify
         Caption         =   "Spacing (s)"
         Height          =   375
         Left            =   120
         TabIndex        =   109
         Top             =   2880
         Width           =   3015
      End
      Begin VB.Label lblWirePairTips 
         Alignment       =   2  'Center
         Caption         =   "Select the differential wire pair that needs to be adjusted in length"
         Height          =   495
         Left            =   240
         TabIndex        =   106
         Top             =   360
         Width           =   9255
      End
      Begin VB.Label lblMinAmplitude 
         Alignment       =   1  'Right Justify
         Caption         =   "Min amplitude (Amin)"
         Height          =   375
         Left            =   120
         TabIndex        =   105
         Top             =   1920
         Width           =   3015
      End
      Begin VB.Label lblSaveAsWirePair 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   7680
         TabIndex        =   104
         Top             =   4560
         Width           =   1695
      End
      Begin VB.Label lblMaxAmplitude 
         Alignment       =   1  'Right Justify
         Caption         =   "Max amplitude (Amax)"
         Height          =   375
         Left            =   120
         TabIndex        =   103
         Top             =   2400
         Width           =   3015
      End
      Begin VB.Label lblType 
         Alignment       =   1  'Right Justify
         Caption         =   "Type"
         Height          =   375
         Left            =   120
         TabIndex        =   102
         Top             =   1440
         Width           =   3015
      End
   End
   Begin VB.Frame tabStrip__Tab6 
      Caption         =   " Teardrop "
      Height          =   5055
      Left            =   9720
      TabIndex        =   61
      Top             =   3720
      Width           =   9895
      Begin VB.ComboBox cmbTeardropPadType 
         Height          =   420
         Left            =   3120
         Style           =   2  'Dropdown List
         TabIndex        =   85
         Top             =   3120
         Width           =   1455
      End
      Begin VB.PictureBox picTeardrops 
         BorderStyle     =   0  'None
         Height          =   2415
         Left            =   5400
         ScaleHeight     =   2415
         ScaleWidth      =   3975
         TabIndex        =   72
         Top             =   1200
         Width           =   3975
      End
      Begin VB.CommandButton cmdRemoveTeardrops 
         Caption         =   "Remove"
         Height          =   450
         Left            =   2760
         TabIndex        =   70
         Top             =   4440
         Width           =   1815
      End
      Begin VB.ComboBox cmbhPercent 
         Height          =   420
         Left            =   3120
         TabIndex        =   66
         Text            =   "cmbhPercent"
         Top             =   1320
         Width           =   1455
      End
      Begin VB.CommandButton cmdCancelTeardrops 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   5160
         TabIndex        =   65
         Top             =   4440
         Width           =   1815
      End
      Begin VB.CommandButton cmdAddTeardrops 
         Caption         =   "Add"
         Height          =   450
         Left            =   360
         TabIndex        =   64
         Top             =   4440
         Width           =   1815
      End
      Begin VB.ComboBox cmbTeardropSegs 
         Height          =   420
         Left            =   3120
         TabIndex        =   63
         Text            =   "cmbSegs"
         Top             =   2520
         Width           =   1455
      End
      Begin VB.ComboBox cmbvPercent 
         Height          =   420
         Left            =   3120
         TabIndex        =   62
         Text            =   "cmbvPercent"
         Top             =   1920
         Width           =   1455
      End
      Begin VB.Label lblTeardropPadType 
         Alignment       =   1  'Right Justify
         Caption         =   "Pad type"
         Height          =   375
         Left            =   240
         TabIndex        =   86
         Top             =   3120
         Width           =   2655
      End
      Begin VB.Label lblTeardropsTips 
         Alignment       =   2  'Center
         Caption         =   "Apply to all pads when deselecting all, otherwise apply to selected pads AND tracks only"
         Height          =   735
         Left            =   240
         TabIndex        =   71
         Top             =   360
         Width           =   9375
      End
      Begin VB.Label lblhPercent 
         Alignment       =   1  'Right Justify
         Caption         =   "Horizontal percent"
         Height          =   375
         Left            =   240
         TabIndex        =   69
         Top             =   1320
         Width           =   2655
      End
      Begin VB.Label lblTeardropSegs 
         Alignment       =   1  'Right Justify
         Caption         =   "Number of segments"
         Height          =   375
         Left            =   240
         TabIndex        =   68
         Top             =   2520
         Width           =   2655
      End
      Begin VB.Label lblvPercent 
         Alignment       =   1  'Right Justify
         Caption         =   "Vertical percent"
         Height          =   375
         Left            =   240
         TabIndex        =   67
         Top             =   1920
         Width           =   2655
      End
   End
   Begin VB.Frame tabStrip__Tab4 
      Caption         =   " SVG/Qrcode "
      Height          =   5055
      Left            =   9360
      TabIndex        =   30
      Top             =   2160
      Width           =   9895
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
         Top             =   2280
         Width           =   3135
      End
      Begin VB.ComboBox cmbSvgHeight 
         Height          =   420
         Left            =   7440
         TabIndex        =   39
         Top             =   2280
         Width           =   2175
      End
      Begin VB.ComboBox cmbSvgSmooth 
         Height          =   420
         Left            =   7440
         Style           =   2  'Dropdown List
         TabIndex        =   38
         Top             =   2880
         Width           =   2175
      End
      Begin VB.ComboBox cmbSvgLayer 
         Height          =   420
         Left            =   1560
         Style           =   2  'Dropdown List
         TabIndex        =   37
         Top             =   2880
         Width           =   3135
      End
      Begin VB.CommandButton cmdCancelSvg 
         Caption         =   "Cancel"
         Height          =   450
         Left            =   4440
         TabIndex        =   34
         Top             =   4440
         Width           =   2175
      End
      Begin VB.CommandButton cmdOkSvg 
         Caption         =   "Ok"
         Height          =   450
         Left            =   1200
         TabIndex        =   33
         Top             =   4440
         Width           =   2175
      End
      Begin VB.TextBox txtSvgFile 
         Height          =   420
         Left            =   1560
         TabIndex        =   32
         Top             =   1500
         Width           =   7455
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
         Left            =   9120
         TabIndex        =   31
         Top             =   1500
         Width           =   495
      End
      Begin VB.Label lblSvgHeight 
         Alignment       =   1  'Right Justify
         Caption         =   "Height (mm)"
         Height          =   375
         Left            =   5160
         TabIndex        =   44
         Top             =   2280
         Width           =   2175
      End
      Begin VB.Label lblSvgMode 
         Alignment       =   1  'Right Justify
         Caption         =   "Mode"
         Height          =   375
         Left            =   360
         TabIndex        =   43
         Top             =   2280
         Width           =   975
      End
      Begin VB.Label lblSvgSmooth 
         Alignment       =   1  'Right Justify
         Caption         =   "Smooth"
         Height          =   375
         Left            =   5160
         TabIndex        =   42
         Top             =   2880
         Width           =   2175
      End
      Begin VB.Label lblSvgLayer 
         Alignment       =   1  'Right Justify
         Caption         =   "Layer"
         Height          =   375
         Left            =   360
         TabIndex        =   41
         Top             =   2880
         Width           =   975
      End
      Begin VB.Label lblSaveAsSvg 
         Alignment       =   1  'Right Justify
         Caption         =   "Save as"
         BeginProperty Font 
            Name            =   "Î¢ÈíÑÅºÚ"
            Size            =   10.5
            Charset         =   134
            Weight          =   400
            Underline       =   -1  'True
            Italic          =   0   'False
            Strikethrough   =   0   'False
         EndProperty
         ForeColor       =   &H00FF0000&
         Height          =   375
         Left            =   6960
         TabIndex        =   36
         Top             =   4560
         Width           =   1695
      End
      Begin VB.Label lblSvgTips 
         Caption         =   "Note:\nOnly for simple images, may fail to convert complex images"
         Height          =   975
         Left            =   1560
         TabIndex        =   35
         Top             =   360
         Width           =   7935
      End
   End
   Begin MSComctlLib.TabStrip tabStrip 
      Height          =   5415
      Left            =   240
      TabIndex        =   1
      Top             =   240
      Width           =   9895
      _ExtentX        =   17463
      _ExtentY        =   9551
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
      Top             =   5790
      Width           =   10335
      _ExtentX        =   18230
      _ExtentY        =   609
      _Version        =   393216
      BeginProperty Panels {8E3867A5-8586-11D1-B16A-00C0F0283628} 
         NumPanels       =   1
         BeginProperty Panel1 {8E3867AB-8586-11D1-B16A-00C0F0283628} 
         EndProperty
      EndProperty
   End
End
Attribute VB_Name = "frmMain"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub chkBulkEditApplyToAll_Click()

End Sub

Private Sub chkInvertedBackground_Click()

End Sub

Private Sub cmbBulkEditTarget_Change()

End Sub

Private Sub cmbFont_Change()

End Sub

Private Sub cmbWirePairType_Change()

End Sub


Private Sub lblBulkEditSaveAs_Click()

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

Private Sub lblSaveAsWirePair_Click()

End Sub

Private Sub tabStrip_Click()

End Sub

Private Sub treRules_DblClick()

End Sub
