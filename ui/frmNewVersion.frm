VERSION 5.00
Begin VB.Form frmNewVersion 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "New version found"
   ClientHeight    =   6150
   ClientLeft      =   45
   ClientTop       =   375
   ClientWidth     =   8760
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
   ScaleHeight     =   6150
   ScaleWidth      =   8760
   ShowInTaskbar   =   0   'False
   StartUpPosition =   2  'ÆÁÄ»ÖÐÐÄ
   Begin VB.CommandButton cmdLater 
      Caption         =   "Later"
      Height          =   495
      Left            =   6240
      TabIndex        =   6
      Top             =   5520
      Width           =   2295
   End
   Begin VB.CommandButton cmdSkipThisVersion 
      Caption         =   "Skip this version"
      Height          =   495
      Left            =   3240
      TabIndex        =   5
      Top             =   5520
      Width           =   2295
   End
   Begin VB.CommandButton cmdDownload 
      Caption         =   "Download"
      Height          =   495
      Left            =   240
      TabIndex        =   4
      Top             =   5520
      Width           =   2295
   End
   Begin VB.VScrollBar vScrlTxt 
      Height          =   3975
      Left            =   8280
      TabIndex        =   3
      Top             =   1200
      Width           =   255
   End
   Begin VB.TextBox txtChangelog 
      BackColor       =   &H00E0E0E0&
      Height          =   3975
      Left            =   240
      Locked          =   -1  'True
      MultiLine       =   -1  'True
      TabIndex        =   2
      Top             =   1200
      Width           =   8055
   End
   Begin VB.Label lblLastest 
      Caption         =   "Lastest"
      BeginProperty Font 
         Name            =   "Î¢ÈíÑÅºÚ"
         Size            =   10.5
         Charset         =   134
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   240
      TabIndex        =   1
      Top             =   555
      Width           =   4455
   End
   Begin VB.Label lblCurrentVersion 
      Caption         =   "Current"
      BeginProperty Font 
         Name            =   "Î¢ÈíÑÅºÚ"
         Size            =   10.5
         Charset         =   134
         Weight          =   700
         Underline       =   0   'False
         Italic          =   0   'False
         Strikethrough   =   0   'False
      EndProperty
      Height          =   375
      Left            =   240
      TabIndex        =   0
      Top             =   120
      Width           =   4335
   End
End
Attribute VB_Name = "frmNewVersion"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
