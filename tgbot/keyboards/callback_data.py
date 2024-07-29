from aiogram.filters.callback_data import CallbackData


class UserAppCallback(CallbackData, prefix='user_app'):
    current_idx: int
    method: str


class ShowAppInfo(CallbackData, prefix='app_info'):
    id: int


class CompletedCommunication(CallbackData, prefix='c_c'):
    id: int


class BackInWork(CallbackData, prefix='b_i_w'):
    id: int


class GradeCallback(CallbackData, prefix='grade'):
    grade: int
    id: int
