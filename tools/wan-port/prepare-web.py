#!/usr/bin/env python3
"""Expose the WR1200JS WAN socket selector independently of IPTV."""
import argparse
from pathlib import Path


def prepare(tree):
    www = tree / 'trunk/user/www'
    page = www / 'n56u_ribbon_fixed/Advanced_WAN_Content.asp'
    text = page.read_text(encoding='utf-8')

    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise RuntimeError('Unexpected WAN page anchor: ' + old[:70])
        text = text.replace(old, new, 1)

    replace('function applyRule(){\n\tif(validForm()){', '''function applyRule(){
	if(validForm()){
		if (wr_wan_socket_supported && document.form.wan_src_phy.value != original_wan_src_phy
			&& !confirm('<#WAN_Socket_Confirm#>')) return;''')
    replace('function change_stb_port_and_vlan(){', '''var wr_wan_socket_supported = '<% nvram_get_x("", "productid"); %>' == 'WR1200JS';
function change_stb_port_and_vlan(){
	// Keep an unsaved selection when IPTV options are edited.
	var wr_selected = document.form.wan_src_phy.value || original_wan_src_phy;''')
    replace('\tshowhide_div("vlan_inet", vlan_filter);', '''	if (wr_wan_socket_supported){
		free_options(o_wsp);
		add_option(o_wsp, "WAN", "0", wr_selected == "0");
		for (var wr_port = 1; wr_port <= Math.min(4, support_num_ephy() - 1); wr_port++)
			add_option(o_wsp, "LAN" + wr_port, "" + wr_port, wr_selected == wr_port);
		showhide_div("wan_src_phy", 1);
	}
	showhide_div("wr_wan_socket_help", wr_wan_socket_supported);
	showhide_div("vlan_inet", vlan_filter);''')
    replace('<tr id="wan_stb_iso">', '''<tr id="wr_wan_socket_help" style="display:none">
                                            <td colspan="2"><#WAN_Socket_Help#></td>
                                        </tr>
                                        <tr id="wan_stb_iso">''')
    page.write_text(text, encoding='utf-8', newline='\n')

    # Without this event a change of the selector alone merely saves NVRAM.
    variables = tree / 'trunk/user/httpd/variables.c'
    text = variables.read_text(encoding='utf-8')
    old = '{"wan_src_phy", "", NULL, FALSE}'
    if text.count(old) != 1:
        raise RuntimeError('Unexpected wan_src_phy event registration')
    variables.write_text(text.replace(old, '{"wan_src_phy", "", NULL, EVM_RESTART_SWITCH_VLAN}'),
                         encoding='utf-8', newline='\n')

    status = tree / 'trunk/user/httpd/web_ex.c'
    text = status.read_text(encoding='utf-8')
    old = '\t\t\tint eth_link = fill_eth_port_status(nvram_get_int("wan_src_phy"), etherlink);'
    if text.count(old) != 1:
        raise RuntimeError('Unexpected WAN link status registration')
    text = text.replace(old, '#if defined(BOARD_WR1200JS)\n'
                        '\t\t\t/* Logical WAN (0) follows the effective driver role. */\n'
                        '\t\t\tint eth_link = fill_eth_port_status(0, etherlink);\n'
                        '#else\n' + old + '\n#endif', 1)
    status.write_text(text, encoding='utf-8', newline='\n')

    strings = {
        'EN': ('Changing the WAN socket interrupts the Internet and may disconnect this session. Move the provider cable to the selected socket; WAN restores the original socket. Continue?',
               'WR1200JS: select WAN or LAN1-LAN4 to replace a damaged WAN socket. The selected LAN socket becomes WAN and the old WAN socket is isolated. Move the provider cable after applying. A socket reserved by a tagged VLAN rule is refused; review IPTV/VLAN settings first. Requires device testing.'),
        'UK': ('Зміна порту WAN перерве інтернет і може розірвати цей сеанс. Переставте кабель провайдера у вибраний порт; WAN повертає заводський порт. Продовжити?',
               'WR1200JS: виберіть WAN або LAN1-LAN4 для заміни пошкодженого порту WAN. Вибраний LAN стає WAN, старий WAN ізолюється. Після застосування переставте кабель провайдера. Порт із правилом тегованого VLAN буде відхилено; спочатку перегляньте IPTV/VLAN. Потребує перевірки на пристрої.'),
        'RU': ('Изменение порта WAN прервёт интернет и может разорвать этот сеанс. Переставьте кабель провайдера в выбранный порт; WAN возвращает заводской порт. Продолжить?',
               'WR1200JS: выберите WAN или LAN1-LAN4 для замены повреждённого порта WAN. Выбранный LAN становится WAN, старый WAN изолируется. После применения переставьте кабель провайдера. Порт с правилом тегированного VLAN будет отклонён; сначала проверьте IPTV/VLAN. Требуется проверка на устройстве.'),
    }
    for lang, (confirm, help_text) in strings.items():
        path = www / 'dict' / ('EN.footer' if lang == 'EN' else lang + '.dict')
        original = path.read_text(encoding='utf-8')
        if 'WAN_Socket_Confirm=' in original:
            raise RuntimeError('WAN socket labels already installed')
        path.write_text(original.rstrip() + '\nWAN_Socket_Confirm=' + confirm +
                        '\nWAN_Socket_Help=' + help_text + '\n', encoding='utf-8', newline='\n')
    print('PASS WAN socket WebUI integration (not device verification)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tree', type=Path)
    prepare(parser.parse_args().tree)
