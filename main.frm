VERSION 5.00
Object = "{831FDD16-0C5C-11D2-A9FC-0000F8754DA1}#2.2#0"; "MSCOMCTL.OCX"
Begin VB.Form frmMain 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "sprintFont"
   ClientHeight    =   4335
   ClientLeft      =   45
   ClientTop       =   375
   ClientWidth     =   8550
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
   ScaleHeight     =   4335
   ScaleWidth      =   8550
   ShowInTaskbar   =   0   'False
   StartUpPosition =   3  '´°¿ÚÈ±Ê¡
   Begin MSComctlLib.StatusBar staBar 
      Align           =   2  'Align Bottom
      Height          =   345
      Left            =   0
      TabIndex        =   18
      Top             =   3990
      Width           =   8550
      _ExtentX        =   15081
      _ExtentY        =   609
      _Version        =   393216
      BeginProperty Panels {8E3867A5-8586-11D1-B16A-00C0F0283628} 
         NumPanels       =   1
         BeginProperty Panel1 {8E3867AB-8586-11D1-B16A-00C0F0283628} 
         EndProperty
      EndProperty
   End
   Begin VB.ComboBox cmbFont 
      Height          =   420
      Left            =   1200
      Style           =   2  'Dropdown List
      TabIndex        =   3
      Top             =   1320
      Width           =   3135
   End
   Begin VB.ComboBox cmbFontHeight 
      Height          =   420
      Left            =   6480
      TabIndex        =   9
      Top             =   1320
      Width           =   1815
   End
   Begin VB.ComboBox cmbLineSpacing 
      Height          =   420
      Left            =   6480
      TabIndex        =   13
      Top             =   2520
      Width           =   1815
   End
   Begin VB.ComboBox cmbWordSpacing 
      Height          =   420
      Left            =   6480
      TabIndex        =   11
      Top             =   1920
      Width           =   1815
   End
   Begin VB.CommandButton cmdCancel 
      Caption         =   "Cancel"
      Height          =   375
      Left            =   4200
      TabIndex        =   15
      Top             =   3360
      Width           =   2175
   End
   Begin VB.CommandButton cmdOk 
      Caption         =   "Ok"
      Height          =   375
      Left            =   960
      TabIndex        =   14
      Top             =   3360
      Width           =   2175
   End
   Begin VB.ComboBox cmbSmooth 
      Height          =   420
      Left            =   1200
      Style           =   2  'Dropdown List
      TabIndex        =   7
      Top             =   2520
      Width           =   3135
   End
   Begin VB.VScrollBar VScroll1 
      Height          =   855
      Left            =   7920
      TabIndex        =   17
      Top             =   120
      Width           =   255
   End
   Begin VB.ComboBox cmbLayer 
      Height          =   420
      Left            =   1200
      Style           =   2  'Dropdown List
      TabIndex        =   5
      Top             =   1920
      Width           =   3135
   End
   Begin VB.TextBox txtMain 
      Height          =   855
      Left            =   1200
      MultiLine       =   -1  'True
      TabIndex        =   1
      Top             =   120
      Width           =   6735
   End
   Begin VB.Label lblFontHeight 
      Alignment       =   1  'Right Justify
      Caption         =   "Height (mm)"
      Height          =   375
      Left            =   4320
      TabIndex        =   8
      Top             =   1320
      Width           =   2055
   End
   Begin VB.Label lblFont 
      Alignment       =   1  'Right Justify
      Caption         =   "Font"
      Height          =   375
      Left            =   0
      TabIndex        =   2
      Top             =   1320
      Width           =   975
   End
   Begin VB.Label lblSaveAs 
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
      Left            =   7560
      TabIndex        =   16
      Top             =   3480
      Width           =   975
   End
   Begin VB.Label LblLineSpacing 
      Alignment       =   1  'Right Justify
      Caption         =   "Line spacing (mm)"
      Height          =   375
      Left            =   4320
      TabIndex        =   12
      Top             =   2520
      Width           =   2055
   End
   Begin VB.Label lblWordSpacing 
      Alignment       =   1  'Right Justify
      Caption         =   "Word spacing (mm)"
      Height          =   375
      Left            =   4320
      TabIndex        =   10
      Top             =   1920
      Width           =   2055
   End
   Begin VB.Label lblSmooth 
      Alignment       =   1  'Right Justify
      Caption         =   "Smooth"
      Height          =   375
      Left            =   0
      TabIndex        =   6
      Top             =   2520
      Width           =   975
   End
   Begin VB.Label lblLayer 
      Alignment       =   1  'Right Justify
      Caption         =   "Layer"
      Height          =   375
      Left            =   0
      TabIndex        =   4
      Top             =   1920
      Width           =   975
   End
   Begin VB.Label lblTxt 
      Alignment       =   1  'Right Justify
      Caption         =   "Text"
      Height          =   375
      Left            =   0
      TabIndex        =   0
      Top             =   120
      Width           =   975
   End
End
Attribute VB_Name = "frmMain"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub lblSaveAs_Click()

End Sub
