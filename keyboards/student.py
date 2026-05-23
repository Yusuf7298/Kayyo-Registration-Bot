from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
sex_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[
            InlineKeyboardButton(text="Male",callback_data="sex_male"),
            InlineKeyboardButton(text="Female",callback_data="sex_female")]])

education_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[
            InlineKeyboardButton(text="School",callback_data="education_school")],[
            InlineKeyboardButton(text="College / University",callback_data="education_university")]])

language_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[
            InlineKeyboardButton(text="Amharic",callback_data="lang_amharic"),
            InlineKeyboardButton(text="Oromo",callback_data="lang_oromo"),
            InlineKeyboardButton(text="English",callback_data="lang_english")]])

availability_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[
            InlineKeyboardButton(text="Full Time",callback_data="availability_full")],[
            InlineKeyboardButton(text="Mon-Fri",callback_data="availability_weekly" )],[
            InlineKeyboardButton(text="Part Time",callback_data="availability_part")]])

department_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[
            InlineKeyboardButton(text="💻 Programming",callback_data="department_programming")],[
            InlineKeyboardButton(text="🎨 Design", callback_data="department_design")],[
            InlineKeyboardButton( text="📈 Marketing", callback_data="department_marketing")]]
)