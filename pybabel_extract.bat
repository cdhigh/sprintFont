D:
cd "D:\Electronic\Soft\Sprint-Layout 6.0\sprintFont"
pybabel extract  --ignore-dirs tests --ignore-dirs build --ignore-dirs docs -o i18n/messages.pot .
pybabel update -i i18n/messages.pot -d i18n
pause
