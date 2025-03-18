import os
import pytesseract  # type: ignore
import cv2  # type: ignore
import numpy as np  # type: ignore
from aiogram import Router, types  # type: ignore
from aiogram.types import FSInputFile  # type: ignore
from aiogram.filters import Command  # type: ignore
from openai import OpenAI  # type: ignore

# Укажи путь к Tesseract, если нужно
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

router = Router()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Отправь мне фото, и я объясню текст на нем.")

from aiogram.types import Message
from aiogram.types import ContentType  # ✅ Верно

# Обработчик для обработки фото
@router.message(lambda message: message.content_type == ContentType.PHOTO)  # ✅ Верно
async def handle_photo(message: Message):

    global recognized_text  # Используем глобальную переменную, чтобы очистить старое значение
    global clarification  # И очищаем предыдущие уточнения

    # Очистка старого текста и уточнений перед обработкой новой фотографии
    recognized_text = ""
    clarification = ""

    bot = message.bot  # Получаем объект бота из сообщения
    photo = message.photo[-1]  # Берем фото лучшего качества
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    await bot.download_file(file_path, "temp.jpg") 
    print("Функция handle_photo вызвана!")

    # Загрузка фотографии с использованием OpenCV
    img = cv2.imread("temp.jpg")

    # Уменьшаем яркость (параметр beta) и увеличиваем контраст (alpha)
    brightness_contrast_img = cv2.convertScaleAbs(img, alpha=1.3, beta=-60)

    # Ядро для резкости 2
    sharpen_kernel = np.array([[0, -0.5, 0],
                               [-0.5, 3, -0.5],
                               [0, -0.5, 0]])  # Резкость 2

    # Применяем резкость 2
    sharpened_img = cv2.filter2D(brightness_contrast_img, -1, sharpen_kernel)

    # Сохраняем обработанное изображение
    output_image_path = 'processed_image.jpg'
    cv2.imwrite(output_image_path, sharpened_img)

    # Распознаем текст с фото
    text = pytesseract.image_to_string("temp.jpg", lang="rus+eng").strip()
    if not text:
        print("Текст не распознан.")
        await message.answer("Прости, но текст не распознан. Попробуй загрузить другое фото.")
        return

    print("Текст распознан:", text)

    # Сохраняем распознанный текст
    recognized_text = text

    # Отправляем сообщение с распознанным текстом
    await message.answer(f"Текст распознан. Что именно вы хотите прояснить?")
    print("Отправлено сообщение с распознанным текстом.")

    # Ожидаем уточнение от пользователя
    @router.message()  # Здесь должно быть исправление - обработчик должен ожидать сообщение с текстом от пользователя
    async def handle_clarification(message: types.Message):
        clarification = message.text.strip()
        
        if not clarification:
            print("Не было получено уточнения от пользователя.")
            await message.answer("Пожалуйста, уточните, что именно вас интересует в тексте.")
            return
        
        print(f"Уточнение от пользователя: {clarification}")

        # Создаем запрос для ChatGPT с уточнением
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Исправь ошибки в тексте, убери все дефисы, цифры и лишние символы, а также постарайся сделать текст более читаемым. Теперь найди часть текста, о которой уточняет пользователь. Необходимо объяснить именно тот момент из распознанного текста, о котором спрашивает пользователь в уточнении. Объясни этот текст как для 10-летнего ребёнка, записав обьяснение не  более чем в 3 предложения. Приведи 3 примера на основе проанализированного текста. Не пиши проанализированный текст, предисловия по типу -теперь я приведу примеры или -давай попробую обьяснить..., пользователь должен получить исключительно твое объяснение с примерами. НО! К примерам правило 3-х предложений не применяется. Вот текст, который отправил пользователь: \n\nТекст:\n{recognized_text} \n\nУточнение: {clarification}."}
            ]
        )

        explanation = response.choices[0].message.content
        print("Объяснение получено от ChatGPT.")

        # Отправляем объяснение от ChatGPT
        await message.answer(f"{explanation}")
        print("Объяснение отправлено пользователю.")
