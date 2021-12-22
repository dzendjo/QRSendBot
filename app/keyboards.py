from rocketgram import MessageType, InlineKeyboard
from rocketgram import context, commonfilters, ChatType, SendMessage


def get_qr_ik(qr_id, T, active_with_sign=True):
    kb = InlineKeyboard()
    if active_with_sign:
        kb.callback(T('process/with_sign_ib', is_active=True), f'go_with_sign {qr_id}').row()
        kb.callback(T('process/without_sign_ib', is_active=False), f'go_without_sign {qr_id}').row()
    else:
        kb.callback(T('process/with_sign_ib', is_active=False), f'go_with_sign {qr_id}').row()
        kb.callback(T('process/without_sign_ib', is_active=True), f'go_without_sign {qr_id}').row()
    kb.callback(T('process/save_ib'), f'save {qr_id}').row()

    return kb