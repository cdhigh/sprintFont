VERSION 5.00
Begin VB.Form frmSettings 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "Settings"
   ClientHeight    =   5835
   ClientLeft      =   45
   ClientTop       =   375
   ClientWidth     =   6750
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
   ScaleHeight     =   5835
   ScaleWidth      =   6750
   ShowInTaskbar   =   0   'False
   StartUpPosition =   2  'ÆÁÄ»ÖÐÐÄ
   Begin VB.ComboBox cmbBackupCount 
      Height          =   420
      Left            =   4200
      Style           =   2  'Dropdown List
      TabIndex        =   13
      Top             =   1920
      Width           =   2415
   End
   Begin VB.Frame frmMcpServer 
      Caption         =   "MCP Server (AI bridge)"
      Height          =   1575
      Left            =   120
      TabIndex        =   9
      Top             =   3240
      Width           =   6495
      Begin VB.CommandButton cmdMcpStart 
         Caption         =   "Start MCP Server"
         Height          =   615
         Left            =   3120
         TabIndex        =   12
         Top             =   240
         Width           =   3135
      End
      Begin VB.TextBox txtMcpPort 
         Height          =   420
         Left            =   1440
         TabIndex        =   11
         Text            =   "5390"
         Top             =   360
         Width           =   1215
      End
      Begin VB.Label lblMcpServerTip 
         Alignment       =   2  'Center
         BackColor       =   &H00EAFFFF&
         Caption         =   "Note: Start the MCP server before the AI client"
         Height          =   375
         Left            =   120
         TabIndex        =   15
         Top             =   1080
         Width           =   6135
      End
      Begin VB.Label lblMcpPort 
         Alignment       =   1  'Right Justify
         Caption         =   "Port"
         Height          =   375
         Left            =   120
         TabIndex        =   10
         Top             =   360
         Width           =   1215
      End
   End
   Begin VB.ComboBox cmbUpdateCheck 
      Height          =   420
      Left            =   4200
      Style           =   2  'Dropdown List
      TabIndex        =   8
      Top             =   2520
      Width           =   2415
   End
   Begin VB.ComboBox cmbEasyEdaSite 
      Height          =   420
      Left            =   4200
      Style           =   2  'Dropdown List
      TabIndex        =   6
      Top             =   1320
      Width           =   2415
   End
   Begin VB.ComboBox cmbLanguage 
      Height          =   420
      Left            =   4200
      Style           =   2  'Dropdown List
      TabIndex        =   3
      Top             =   720
      Width           =   2415
   End
   Begin VB.CommandButton cmdSettingsCancel 
      Cancel          =   -1  'True
      Caption         =   "Cancel"
      Height          =   495
      Left            =   3600
      TabIndex        =   1
      Top             =   5160
      Width           =   2295
   End
   Begin VB.CommandButton cmdSettingsOk 
      Caption         =   "Ok"
      Height          =   495
      Left            =   480
      TabIndex        =   0
      Top             =   5160
      Width           =   2295
   End
   Begin VB.Label lblBackupCount 
      Alignment       =   1  'Right Justify
      Caption         =   "Backup Count"
      Height          =   375
      Left            =   240
      TabIndex        =   14
      Top             =   1920
      Width           =   3615
   End
   Begin VB.Label lblUpdateCheck 
      Alignment       =   1  'Right Justify
      Caption         =   "Update check (days)"
      Height          =   375
      Left            =   240
      TabIndex        =   7
      ToolTipText     =   "Double Click To Check Now"
      Top             =   2520
      Width           =   3615
   End
   Begin VB.Label lblEasyEdaSite 
      Alignment       =   1  'Right Justify
      Caption         =   "EasyEDA server"
      Height          =   375
      Left            =   240
      TabIndex        =   5
      Top             =   1320
      Width           =   3615
   End
   Begin VB.Label lblLanguageTips 
      Caption         =   "These settings will take effect after restarting"
      ForeColor       =   &H007C7C7C&
      Height          =   375
      Left            =   240
      TabIndex        =   4
      Top             =   120
      Width           =   6255
   End
   Begin VB.Label lblLanguage 
      Alignment       =   1  'Right Justify
      Caption         =   "Language"
      Height          =   375
      Left            =   240
      TabIndex        =   2
      Top             =   720
      Width           =   3615
   End
End
Attribute VB_Name = "frmSettings"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Private Sub lblUpdateCheck_DblClick()

End Sub
