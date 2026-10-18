#!/usr/bin/env python3
"""Expose Cron process presence separately from scheduled-job success."""
import argparse
import ast
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user'
backend=root/'httpd/web_ex.c';text=backend.read_text(encoding='utf-8')
anchor='struct ej_handler ej_handlers[] =\n'
entry='\t{ "json_system_status", ej_system_status_hook},\n'
assert text.count(anchor)==1 and text.count(entry)==1 and 'ej_wr_cron_process_state' not in text
handler=r'''
static int wr_process_present(const char *name);
/* Cron process presence never proves execution of a scheduled job. */
static int ej_wr_cron_process_state(int eid,webs_t wp,int argc,char **argv)
{
 int requested,active;
 (void)eid;(void)argv;
 if(argc!=0 || access("/proc/self/stat",R_OK) || access("/usr/sbin/crond",X_OK)) return websWrite(wp,"3");
 requested=nvram_get_int("crond_enable")>0;
 active=wr_process_present("crond");
 if(active<0)return websWrite(wp,"3");
 return websWrite(wp,"%d",active?(requested?1:4):(requested?2:0));
}
'''
text=text.replace(anchor,handler+'\n'+anchor,1).replace(entry,entry+'\t{ "wr_cron_process_state", ej_wr_cron_process_state},\n',1)

# Reuse the existing bounded observer UI and locale structure as literal data,
# without executing another preparation script or copying its SSH backend.
template=ast.parse(Path(__file__).with_name('prepare-ssh-status.py').read_text(encoding='utf-8'))
def literal(name):
 return next(ast.literal_eval(n.value) for n in template.body if isinstance(n,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
script=literal('script').replace('wrSSH','wrCron').replace('WRSSH','WRCron').replace('wr_ssh','wr_cron').replace('!found_app_sshd()','false')
translations=literal('translations')
notes={
 'EN.footer':'Shows the saved Cron setting and whether crond is present. Scheduled-job execution, timing and results are unverified. Observations expire after 45 seconds; refresh every 30 seconds while visible.',
 'UK.dict':'Показує збережене налаштування Cron і наявність crond. Виконання завдань, правильність часу й результати не перевірені. Дані застарівають через 45 секунд; оновлення кожні 30 секунд у видимій вкладці.',
 'RU.dict':'Показывает сохранённую настройку Cron и наличие crond. Выполнение заданий, правильность времени и результаты не проверены. Данные устаревают через 45 секунд; обновление каждые 30 секунд в видимой вкладке.'}
present={'EN.footer':'Enabled; crond present (jobs unverified)','UK.dict':'Увімкнено; crond є (завдання не перевірено)','RU.dict':'Включено; crond есть (задания не проверены)'}
page=root/'www/n56u_ribbon_fixed/Advanced_Services_Content.asp';html=page.read_text(encoding='utf-8')
row='<tr id="row_crontabs" style="display:none">'
initial='\tchange_crond_enabled();'
assert html.count(row)==1 and html.count(initial)==1 and 'wr_cron_process_status' not in html
status='''<tr id="wr_cron_status_row"><th><#WRCronObservedTitle#></th><td>
<strong id="wr_cron_process_status" role="status"><#WRCronUnknown#></strong>
<button type="button" class="btn" onclick="wrCronRefresh()"><#WRCronRefresh#></button>
<small id="wr_cron_observed_at"><#WRCronNoObservation#></small>
<p class="help-block"><#WRCronObservedNote#></p></td></tr>
'''
assert html.count('function applyRule(){')==1
html=html.replace(row,status+row,1).replace('function applyRule(){',script+'\nfunction applyRule(){',1)
html=html.replace(initial,initial+'\n\twrCronRender(<% wr_cron_process_state(); %>);\n\twindow.setInterval(wrCronRefresh,30000);',1)
for language,values in translations.items():
 values={key.replace('WRSSH','WRCron'):value.replace('SSH','Cron') for key,value in values.items()}
 values['WRCronObservedNote']=notes[language];values['WRCronPresent']=present[language]
 path=root/'www/dict'/language;content=path.read_text(encoding='utf-8')
 assert 'WRCronUnknown=' not in content
 path.write_text(content.rstrip('\n')+'\n'+'\n'.join(key+'='+value for key,value in values.items())+'\n',encoding='utf-8',newline='\n')
backend.write_text(text,encoding='utf-8',newline='\n');page.write_text(html,encoding='utf-8',newline='\n')
print('Prepared Cron process observation; scheduled jobs and physical runtime unverified')
