#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
导线对长度调整的图片数据
"""

singleWirePairImageData = """
R0lGODlh9QCiAPcAAAAAAAMAANsPE+AUFu4YGeYYGuwZHOYbHu4dHukdHtwcIOQeIucgIeYiJewmJ90k
JcYlJus2OetGSeQDCukLEu0TGuUVG/QZIusYIeIaH+0eI+IgJessMuc9ROVESvFRV+FNUqY+QtNqbvAK
Fd8SHeUYI+4hL+YgKuQiLfQpNOQwO/5nb4lrbe0PH+oYJ8Ogo/AXLfVWZi4tLomKkhkaG72/wQ8QEOYq
EeUzG9sZA+MbBOwdB+EgCeAkDOUiDeckD9smD9gpE+AqFd0yHOISAuEaCeceCuUaCt0cC+AcDdgdDd0g
D+0hEeohEeEjEOkmE+QiEucjE9kgEu0nFuUoGN4lF9coGuwuHuZGOPNrX+6RidoTBO0UBekWCeIVCfEW
C90VCuMZDeoZDuYeD+4dEOkdEuUcEeEbEeEfEecgE+AhE/IkFeogFeMfFOAfFNwdE+UhFeQiFeIhFech
FuMkFuUjF94iFucjGNsjF+klGeYkGesnG+ElGtUkGuUnHeIpHdwpH+ItIeYzJu0yKNkyJ+g1K+ZMRORW
T+AKAe0LA+ULBeUQB+IQCOQUDOETDecYDuUXD+kbEeIWENwXEO0ZEvMbFOodFOcZE+QcFOMdFOAcFO8c
FugaFeceFecdFeUeFfAgF+weF+cfFuUfFuUcF+UgF94fFvkgGukeGOgdGOIfF+AcF+khGeUfGe8iG+Ii
Gd0eGeYjG9wiG+okHu8mIOAmHuAjHugnIOEoIeoqJOUuJeo6NOQ3Mt84M/JHQutLRelQTO9VT/daVulb
VullYPd1b+18d+QGAekFBPYIBt0JCOUNCukNC+wTDuYRDtoPDeAPD+cTEeoWE+UWEtIUEewZFeQYFecX
FuIaFuscGOccGOoZGfAfG+AZGfEcHOwcG+gcG+geG+seHOUdG+IfG+whHeUfHOAeHOghHuUeHuQiHvUj
I+EiIesjI+UnJuorK+AtLOw0Mvg6Nu86OuY7O9o6OexFQeVFQu1LSc9LS+9hXtxeXvN2dGxraw0NDf//
/yH5BAEAAP8ALAAAAAD1AKIAAAj/AP8JHEiwoMGDCBMqXMiwocOHECNKnEixosWLGDNq3Mixo8ePIEOK
HEmypMmTKFOqXMmypcuXMGPKnEmzps2bOHPq3Mmzp8+fQIMKHUq0qNGjSJMqXcq0qdOnUKNKnUq1qtWr
WLNq3cq1q9evYMOKHUu2rNmzaNOqXcu2rdu3cM0SCnQFlKtBg/404IAvqa9AfwLpcvculztdET7EDTnM
kCAwYLwsWuQFzBZn0ca9m6dY6DAsg6BsKXKkESRJzpotKlKlkD19izfKU3YMWTR07GydG0cKkxw/sbBJ
apZIGaGfwso9gzZNlZ095TyJeqPGVRMeSMIompChL0Eb4MPb//BHnjyA8+jTq1/Pvr379+h9kkj0ZQwm
Ahc0pDuXrt26da7UYQccoKzxAxJLtGPPTsRUcgEMJDTAQALiiMMKKpwsAUQUoVAijSe00ILKNG9AEEI/
/cCn4oostqgeTxKg4IIFcjzxAxTkLBBKJaCwQYcaqnBSTSqquKEKKpawEYsDvtwUgwl+kGEJNqb4oQcq
rmCiiSiolBOLKa+U4w0nbajhhBFdTAKBCDXE5hAWXkTjDSmv0NKGEz0QkcieiPSJiCLLQJLEGeHkgk4m
SXTBzC42SYNIEqmkAQUddtiRSTTIHMNIHNFMoAxm0Vyiiix2xBIOJlLIs4KbDKmgihFMMP8xxijpDEAK
FTi49oshhuBjjz1Y7JKLJ5zcos4qZ0SRxCTwCCOTMMfwIAQfGczxRCdgrOIOB/P4cggxh3Twyy+76HIL
Oumks8AJDaiRSDIpsJpQBN5ccoYmdfiBhxLXaCDBQjHAI0kF3mRTzSmowEJYTB80o4MPoSQAix1oTCON
Bt4lhE8D11RDBgEYnHHDDWagIK9BHjyygzcHmMKHNMwwANtDv1ijCBt1VPEKK2LE89IHDyihiTjfpFKH
Io7cAxEwrxDBBShVWPEKARXMfPI/HljwiA+0oIPEI+10FhExGSwjRRWxzLFDI/S4tMwkuCSAgDaTTOMB
RSD4wUUVsiz/cAEls1z9jz6sXIPOHH6gUcQexFREzAa1xCJOKWk4oQYCLOFgRDUaeFOJKrC8Y9E+R0CB
CgPo7MCF6CefAMgb1rBCBzMOZETPNZGYYU4sbVizkj5jCIFHN9I0Y0DGFQXTyiSmkANKGLaIHRsw0GxA
sStd0LIRPIisscACmFizYEoNXCIKqWMs829GwvCxBSzpkPNJ7axyYgYGdTjxzSNZcBRFJSVQACc20YiU
FAIR6KhAAugghEJwxBBIUIUCGLAJMfTCTfNIxBQQUIozFIAXHckCMxSggGycAhH1QMkfuoCACyAgDIHw
SCG4sYADWOIG2otNIejThldcgwEfiYcV/2SRgDXoQBYnqYcQIlEBBFTBDuvjSBYocA1svAEIzZCeW4CB
gyN0oQes8BdIBBGJBPDACWcAYUkwUAVUVIATSsACSAwgjTZUAQ/M4MBidBEFOJiiB5SIF0jk8QVUKKEK
Y7iFSS5whgRcABKIaNxHgrGHJtzCFtMwhyTfAg4ysEIBQkjEPEKSQTbAAhZmuEJJDtEMUWhAA1U4hkh2
4QVJwAId2fhFXLrxhW+cQB3ICEZI9BEGMZxgAWHYg9VCco8kNEEc6agC/UCyC0ScoR1zWITP4HKOZmSj
AeAooEh40QUTtMMMetDlSHYBhDFooxuYGIZI7gEGNqzDDIqYZluKEf+kUsghFGoMySG6IA5ztMIPgyAJ
JdzQhgRsIxLGEMk+bFENSmjjEgl9SxZIwYlSqMESbRPJMBYRDnOs4hW6IEkzGOrQMpAEFxVthTUGEdGS
BOCmOA2AZ0hxCX9eYnwhyQJJTWqKP5CEGW6QQziu4dKR6KIaZWjFNHJRU5LkNKdBAQZPSzEKSDRpJCRF
BzleYdSRKKINchgHU0lSCEpEQqpUtelVcRoUQ1wiEqwQBSSAGpJFpIMBs7hFDM0qijqYwxpmIEk8pJEG
VUAirlad602D8otLXOJCl1AaWMfBgFvkIqUjOQYr6iDVxK5zGml4xWOrKhLJ0vUn+LgEJlgRCk7/aFYk
i+CsZ0ErEtHeobQk2UU04KBayLbWtZOFrWznEIpQ3Lavf1WHHwbbW1bcYRzTMO0so1GHV0TDuCG56j/E
C1tPtEEU1diEIUjSiHY0QB18oG5IRDsH7Go3JLyIhh5K4QzwgkS8c4UtK+LQhmhQYr0jYYQDHKCOopIE
EVwFx1pHkt88qKK/rP1IgAPsE3zMog6YmMYl1CkSBb+jwbV48Cg+IeGmjjMaFsbwSMg7Xqx2uBSdQIUn
MMFXkCjYHbZ4RYpDO4c5HDYSwX2EKPSaC34c18Y1hvJO8FEKT6BCFJno8UcW4YB34IIPuCDJMYp85CRL
57FODq+UOcwTKlu5/xNZJski2vEOd/yBt/MlszWQvM5HdILJaf6vlKOc3DZXGRVw1rJHFsGAwtxZzHrm
8yz9DGg1D5rNOnEzouOcYHUcRjCQNvKek/xnNFu60APBdE40nWiSMIIch9GFfEEyZlFLOiS7oLSpBf3a
gqj6JqzmdInNwQ5dCGLWH6l1mftc6ibzutcE+bVNgq3ojiyC2LgQBJ5pHWlSV1rDyEWuod8s7L7iphbG
DvWyJ93sQHMk3PCesirIXW2OLCIBufmDA4lsa2/vuiPwDveUD43lem9EEeBggC1qse/ednudkOhEK/79
7oC7dsoEUIIdEOBVkixjFaAIxQME8WBUFPQM9/8FSSHAoA4GSOMKGc6ItKNN45vYQxo98IMGzGBwjSxD
FUywxAZYFxJiICIb3yDHGS7BVi+0/OUxx8jMU11zm9jjEkwoxwGgQOK+xgIOmUhHDot+DHEQ6QzVCK4Y
UjEOSfxhkxuZukDkDhNfuIISFuhGEZw1ki+g4xV0KEczRkKMY5RDFHIwAwFIMo9mcAIbk+ADCABedYTQ
3SWCyMMlDjCOLfRvJFwgByzkwAZZikQfx1DFKOJghgqQxB7N2MQo3OCHDlB+0Jav/EwaAQh1aCAcOfi8
SBChG0yMQREjEcYiYPGJNJghAyTBBzMqcYdXzEIFt4d2Qi7fEmQQAh4O4AT/D0oyiUC43Isj8YUXzkGK
SHwCHiQZhjIq0d1ynMAtwUAGLggBCGs8oiS8oAsONQaP0HUe8RgMkApi4AeTRxLPQAZtoAmc0A1ugQVi
4ACEQAifsAwloQ+AUADf0ARnEGYggQ9IgAQNIA7N0HAjwQ5k8AmqcAnTsExpcQWukAK9QAi30AAmgQvd
gA5ssAqTIE8fcQtEkAYNoAHLIEclMQ9M0AqxwAbSEAFsQQ+LwAoqAA98MAh8p1jqYAuXQA6SwIQesQdf
sAkLwADKQIbplwbYQA5sQAklwBbu4AVq0ADwUACjZBKHcAXc0A0KgAZXIEwd8QCgUA2kwAqsQAFaJBIY
/yAJYyAGaxANtpcWDbANpRAHkfAG7BADKFEIzHAO7BAHRsAKHXEIiFAJrPAK2uAIVHgSKsAJYhAJTBAJ
C9CAZuELX1ABGrAHY7AFKYQShqAMoUALoSAJ7KAAG0EM7gAO1fAEemABAqAS71AN5oAJeZAHskCIZPEB
i7AD+SEEN5AM+aASCnAKaAAHF4ABzlCJGNEL2EAJUbAEZ4AO2JcSEiAAVYAOrOAEPDAEZRED7QAG+wgL
SuADCCACKgEBzcADS7ANFxAJfHA3FyEjBtAETyAFjLB4K8EOPFAOBTANsbJNYeELyfAItvAAVbAEYdAA
+/ACKhEC8UAFSCAJ3KAHPf+ABJNQEfpQAAKQH1VwIKqAPCgxDGOgCgVgANxQCeHQC/sAFvEwBU8QCRZQ
AnTABOvwAS/QJinBAlrAC2PQBFKgCWnQA0rgAI3IEA5gAAhQCWWAB33gBIxggCkxD32AULJwDt/gDQaQ
AFyxAh/AC4DwB3nwB+pwDWGQDHzHlSdBAwOhC4qQB+JQAKSwDuAgC71AgwlxCPBQCZJgB1PQBE6ABs7g
ei+hAotgBGWkAd8gCV3wDrhYFcNgAiMQDXyQge6AC3RgBgPgjjOAEudBEByQAOBwACWQAuIABozgDIPA
jQcBDIDgBWKQDVUQBHSQBl0QSDIxD14ABaqQDuagBlH/8AjKcAu+IHxHkQVYMESFIAiqQBvI0AzbYEXx
BQ/2mQ6eoAsU+Q/BeRL9ORAqwFAH0ADlUAmWkARbsAwX0AIW8AeDMAvOMAHM0AyC4gNRsAp/QAWXIAmc
IA80QQ+AoARnwAqx8ApykAaWcAnRQAEUQADlcAtDEAgpAAPuyBMqcGLggABzc1KxkA3SYAl2UAregA7q
cAu6oA6s4Jz/WRJLKhBUQAQ+MAZwEAvoEA7ooAdIcARMwAqdEAmPMAZjgAatMAsJUACbkAAJwAnHQJIz
8Q5fwAVpkAALAIdp4AamcA7kMA7jgAqhMAd8YAqt8A41ihMfQAHWYA2XkF7V0Alw/5AHrBAOC9AArEAG
XtQMkxBSBNGkI6Gp/8BKjjAJaqAHebAHsfAGr4AO28AJZSApTuAEdUCmBfAEzEABJpCWMvEOykABlwAH
cAAFaqAGlSIHrYAKBFCsmnAGFdACT8mfLuIiGGEPyNAKeQUHc8AGbNAJncAK5gCelvAIRLAH9rCsBcGp
IUGuwnAPD6AJZgCmbhALDJCAqMAKbCApvxpi0zAHtxBFOQEC8zAHXsAJpFAmTgAFc4AK4QAO4EAAnkAH
6EAB5ciszcoiGUEN2lAOsxALmvAG7YoO43AGPMADnqABJuCJCEGuIGGyAsEBB2ANGgIFlVAJVBAHZWAJ
ljAHr/9wpwegAYLkEx5AAut4AOZQDq7ADdXACeRQBUDgA03QBgKgBTxRD8egCIzACF5QtVOrCFJLC1+l
ECjrEV0rEMLwDtBQG0jzDGarDBNAAScADEZxCA8wAciADIsAGcrZBYlwDM+gmTiRBcNwCMAQDMIQDIcw
DOjJEF/LEYdrEPowDMMAd0uhD4t7CMEQDMMADESIFYmrEZkrOEGxuRjhuZzrE6BrEaMbujtRuhSBuqaL
E6orEa27ujXxuhAhu7ArE7TrELdbuy+Ru4YLALqbFLy7EMH7uyqxuQHXu8R7FIlrcTolvL6bvEVxuMzb
vFz7vNA7FF87vdSbEMN7vUxqvbn/J1m+hmolC77e+xNdK76Wh7zn27nmaxDcV73t674LEb/c+77zqxPp
q3uzi7/5y7r+S3X8i7sB/L+xW8CENsDOa8A9kb3iFhHdy8CIi8BzJ3APEcESrLkUXMEWzL4ZDMAPcbwe
/ME24bnxtsAkfBOl+8D3m8IqvMHbR3cY7MKpC8MxjHvjasM0bBKtK8M6vMMk0cMKzKxAPBPpW79DPMNF
fMEIjMPq28JLDBP7q70oHMUuMcXMO8JWvBJYLMJVvMVc3MQWx8Rg3BLGi8NaXMb++cMXocRqfBBuPBBx
/MaZysaka8d0fMfAicd5XMMpwcd9HMiCPMiEXMiGfMiInMiKJbzIjNzIjvzIkBzJkjzJlFzJlnzJmJzJ
mrzJnNzJnvzJoJzBAQEAOw====="""

doubleWirePairImageData = """
R0lGODlh9QCmAPcAAAAAAAMAAOsFCOcMDt4ND+YPE+kTFOoZHNoZGvAdIeAeH+wiJeMhI+4mKfM1OeUz
N+8/QO1bXPNpauQDCvALEvASGuQTGvAYHvcaIuYbIOkeI/wqMtorMe4zOyEJCuhCR9lCSd1GTOxNU+5V
WuVVWftzePJvdelrb7NfYeUhLNohLOQpNuE7Q/ReaOAZKPVMWb89R+ZDVC0qLBgdIA0ODh4jIaydlOAZ
BOsfB9ogDOMmD98sFutSPtoYBd8cC+YeDd8fD+UhEeIiEtcjE+cmFeImFdskFe8oGOQpF+QsHtgyI9xB
M+hSRuQOAesRAuQRA+cWB+kYCuMXCd8UCvMaDO8XDNkWC+kYDeoaDuMbDu0eD+kdEecdEuMcEuIdEvAg
FOsfFOQeE98gE+cfFOsiFuYhFeMiFecjGOIjF94iGOQjGeMmGt8nGt4kGucoHOopHtsoHOQpHuEvIuk1
KOo9MvJCNuc/NuVCOelGO+1GPe9IP+pJPuNGPehIP+pOQ/ZUTOtVTO9mXd5hWM91cOkLBfMOBt4PBuoO
COgRCOYSCeUVDeAWDukYEOYaEO0XEeEZEOYZEuwbFN8cE+gcFNscE+kaFeUdFeQdFeIbFewcF+geFuYc
FusfF+kcF+ceF+QeF+EeFvEgGeQhGN8gF+ogGegfGecgGeYeGewhG+ciG+cgG+UjGuMgGuIhGt4gGusl
HOkhHOYkG+UhG+clHPElH+IiHeYkHuslIOAnINQjHusrIuQtJugvKuE1MOw+OOlBOepEPexDPuNSS+1W
UupZUuNZVO1xbPJ1cfN/e+l5drcBAEkAAOsCAeMEAtkJBuQKCesQC+IRDOwSDeUSD/AUE+kYE+MVE+4Z
Fd4XFPQaF+cYFu4dGeUcGOkaGeUZGe8bG+ofG+IdGuUeHOgeHuUiHvUhIe4iIOgjIdsiH+MlIfMxLeYs
LOszMdU2NO87O+Q7OelAPe9DQ+RCQPJLSOxJR+RHRulLS+pRTvVYWOVeW+hnZBgNDRkYGAcHBwICAv//
/yH5BAEAAP8ALAAAAAD1AKYAAAj/AP8JHEiwoMGDCBMqXMiwocOHECNKnEixosWLGDNq3Mixo8ePIEOK
HEmypMmTKFOqXMmyZclkLmPKnDnzHrty1J45czYglLld8ALRHEq0qMUIHBiYo/XlkZF04xC4osXJBxBa
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="""
