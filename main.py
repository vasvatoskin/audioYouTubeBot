import logging
from aiogram.methods import SendAudio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, FSInputFile
from pytube import YouTube, exceptions
import os, subprocess
from bot_answers import *

API_TOKEN = input(TOKEN_INPUT_PROMPT)
dp = Dispatcher()
logger = logging.getLogger(__name__)

authorized_user_id:   dict = {}
unauthorized_user_id: set = set()
user_pin:             str = str((input(PIN_INPUT_PROMPT)))
out_audio_quality:    int = 50

async def access_guard(message: Message) -> bool:
    if message.from_user.id not in authorized_user_id:
        if message.from_user.id not in unauthorized_user_id:
            await message.answer(GUARD_ANSWER_PIN)
            unauthorized_user_id.add(message.from_user.id)
            return False
        else:
            if user_pin == message.text:
                await message.answer(START_ANSWER.format(message.from_user.full_name))
                authorized_user_id[(message.from_user.id)] = "Here you can save the settings for the user. The key value is not currently used."
                unauthorized_user_id.discard(message.from_user.id)
                return False
            else:
                await message.answer(GUARD_ANSWER_ERROR)
                return False
    else:
        return True

# COMMAND
#
@dp.message(commands=["start"])
async def command_start_handler(message: Message) -> None:
    if await access_guard(message):
        await message.answer(START_ANSWER.format(message.from_user.full_name))

# LOGIC
# 
@dp.message()
async def logic_bot(message: types.Message):
    if await access_guard(message):
        try:
            yt_object = YouTube(message.text)
        except exceptions.PytubeError:
            await message.answer(INVALID_LINK)
            return

        stream = yt_object.streams.filter(only_audio=True)[0]
        file_name: str = stream.default_filename.replace(" ", "_")
        stream.download(filename=file_name)
        file_size: float = round((os.stat(file_name).st_size / 1000000.0), 2)

        if file_size < 50:
            file = FSInputFile(file_name)
            await SendAudio(chat_id=message.from_user.id, audio=file)
            os.remove(file_name)
        else:
            num_parts: int = int(file_size // 50)
            for parts in range(num_parts + 1):
                part_duration = 2
                output_file = str(parts) + "_" + file_name[: -1] + "3"
                input_file = file_name
                start_time = part_duration * parts
                stop_time = part_duration * (parts + 1)

                command = f"ffmpeg -i ./{input_file} -ss 0{start_time}:00:00 -to 0{stop_time}:00:00 -ab {out_audio_quality}k -ac 1 {output_file}"
                subprocess.call(command, shell=True)

                file = FSInputFile(output_file)
                await SendAudio(chat_id=message.from_user.id, audio=file)
                os.remove(output_file)

            os.remove(file_name)
def main() -> None:
    bot = Bot(API_TOKEN, parse_mode="HTML")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
