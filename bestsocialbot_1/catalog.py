import json
from aiogram import types, F
from aiogram.types import CallbackQuery, InputMediaPhoto, InputMediaVideo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite
from dispatcher import dp
from utils import check_blocked_user

@dp.callback_query(F.data.startswith("item_tech_"))
async def show_product_details(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    item_id = int(callback.data.split("_")[-1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT ap.title, ap.description, ap.price, ap.category_id, ap.user_id, ap.contact_info, u.username, c.name, ap.images FROM auto_products ap LEFT JOIN users u ON ap.user_id = u.user_id LEFT JOIN categories c ON ap.category_id = c.id WHERE ap.id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await callback.answer("Предложение не найдено", show_alert=True)
        return
    title, description, price, cat_id, user_id, contact_info, username, cat_name, images_json = item
    
    # Парсинг изображений
    images = {}
    if images_json:
        try:
            images = json.loads(images_json)
        except:
            pass
            
    text = f"📦 **{title}**\n\nКатегория: {cat_name or 'Не указана'}\n"
    text += f"Цена: {price}₽\n" if price else "Цена: Не указана\n"
    text += f"\n{description}\n" if description else "\n"
    text += f"\n👤 Продавец: @{username}" if username else f"\n👤 Продавец: ID {user_id}"
    if contact_info:
        text += f"\n📞 Контакты: {contact_info}"
        
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="catalog_tech"))
    
    # Удаляем предыдущее сообщение с меню
    try:
        await callback.message.delete()
    except:
        pass

    # Отправка основного фото
    sent_main = False
    if images.get("main"):
        main_photo = images["main"]
        try:
            if main_photo["type"] == "photo":
                await callback.message.answer_photo(photo=main_photo["file_id"], caption=text, reply_markup=builder.as_markup())
            elif main_photo["type"] == "video":
                await callback.message.answer_video(video=main_photo["file_id"], caption=text, reply_markup=builder.as_markup())
            sent_main = True
        except Exception as e:
            print(f"Error sending main media: {e}")
    
    if not sent_main:
        await callback.message.answer(text, reply_markup=builder.as_markup())
        
    # Отправка дополнительных фото
    if images.get("additional"):
        media_group = []
        for img in images["additional"]:
            try:
                if img["type"] == "photo":
                    media_group.append(types.InputMediaPhoto(media=img["file_id"]))
                elif img["type"] == "video":
                    media_group.append(types.InputMediaVideo(media=img["file_id"]))
            except:
                pass
        
        if media_group:
            # Отправляем альбомом
            # Ограничение телеграм - 10 файлов, у нас макс 3
            try:
                await callback.message.answer_media_group(media=media_group)
            except Exception as e:
                print(f"Error sending media group: {e}")

    await callback.answer()

@dp.callback_query(F.data.startswith("item_service_"))
async def show_service_details(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    item_id = int(callback.data.split("_")[-1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT as_.title, as_.description, as_.price, as_.category_id, as_.user_id, as_.contact_info, u.username, c.name, as_.images FROM auto_services as_ LEFT JOIN users u ON as_.user_id = u.user_id LEFT JOIN categories c ON as_.category_id = c.id WHERE as_.id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await callback.answer("Предложение не найдено", show_alert=True)
        return
    title, description, price, cat_id, user_id, contact_info, username, cat_name, images_json = item
    
    images = {}
    if images_json:
        try:
            images = json.loads(images_json)
        except:
            pass

    text = f"🛠 **{title}**\n\nКатегория: {cat_name or 'Не указана'}\n"
    text += f"Цена: {price}₽\n" if price else "Цена: Не указана\n"
    text += f"\n{description}\n" if description else "\n"
    text += f"\n👤 Исполнитель: @{username}" if username else f"\n👤 Исполнитель: ID {user_id}"
    if contact_info:
        text += f"\n📞 Контакты: {contact_info}"
        
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="catalog_services"))
    
    try:
        await callback.message.delete()
    except:
        pass

    sent_main = False
    if images.get("main"):
        main_photo = images["main"]
        try:
            if main_photo["type"] == "photo":
                await callback.message.answer_photo(photo=main_photo["file_id"], caption=text, reply_markup=builder.as_markup())
            elif main_photo["type"] == "video":
                await callback.message.answer_video(video=main_photo["file_id"], caption=text, reply_markup=builder.as_markup())
            sent_main = True
        except Exception as e:
            print(f"Error sending main media: {e}")
            
    if not sent_main:
        await callback.message.answer(text, reply_markup=builder.as_markup())
        
    if images.get("additional"):
        media_group = []
        for img in images["additional"]:
            try:
                if img["type"] == "photo":
                    media_group.append(types.InputMediaPhoto(media=img["file_id"]))
                elif img["type"] == "video":
                    media_group.append(types.InputMediaVideo(media=img["file_id"]))
            except:
                pass
        
        if media_group:
            try:
                await callback.message.answer_media_group(media=media_group)
            except Exception as e:
                print(f"Error sending media group: {e}")

    await callback.answer()

@dp.callback_query(F.data == "catalog_tech")
async def catalog_tech(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM product_purposes ORDER BY id")
        purposes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if purposes:
        for purpose_id, purpose_name in purposes:
            builder.add(types.InlineKeyboardButton(text=purpose_name, callback_data=f"purpose_tech_{purpose_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет категорий", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    await callback.message.edit_text("📦 **Каталог товаров**\n\nВыберите категорию по назначению:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("purpose_tech_"))
async def catalog_tech_purpose(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    purpose_id = int(callback.data.split("_")[-1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_purposes WHERE id = ?", (purpose_id,))
        purpose = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM product_types ORDER BY id")
        types_list = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if types_list:
        for type_id, type_name in types_list:
            builder.add(types.InlineKeyboardButton(text=type_name, callback_data=f"type_tech_{purpose_id}_{type_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет подкатегорий", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_tech"))
    purpose_name = purpose[0] if purpose else "Категория"
    await callback.message.edit_text(f"📦 **{purpose_name}**\n\nВыберите подкатегорию по типу:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("type_tech_"))
async def catalog_tech_type(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_types WHERE id = ?", (type_id,))
        ptype = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM product_classes ORDER BY id")
        classes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if classes:
        for class_id, class_name in classes:
            builder.add(types.InlineKeyboardButton(text=class_name, callback_data=f"class_tech_{purpose_id}_{type_id}_{class_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет классов", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"purpose_tech_{purpose_id}"))
    type_name = ptype[0] if ptype else "Тип"
    await callback.message.edit_text(f"📦 **{type_name}**\n\nВыберите класс:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("class_tech_"))
async def catalog_tech_class(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    class_id = int(parts[4])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_classes WHERE id = ?", (class_id,))
        pclass = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM product_views ORDER BY id")
        views = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if views:
        for view_id, view_name in views:
            builder.add(types.InlineKeyboardButton(text=view_name, callback_data=f"view_tech_{purpose_id}_{type_id}_{class_id}_{view_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет видов", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"type_tech_{purpose_id}_{type_id}"))
    class_name = pclass[0] if pclass else "Класс"
    await callback.message.edit_text(f"📦 **{class_name}**\n\nВыберите вид:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("view_tech_"))
async def catalog_tech_view(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    class_id = int(parts[4])
    view_id = int(parts[5])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM product_views WHERE id = ?", (view_id,))
        pview = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM product_other_chars ORDER BY id")
        others = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if others:
        for other_id, other_name in others:
            builder.add(types.InlineKeyboardButton(text=other_name, callback_data=f"other_tech_{purpose_id}_{type_id}_{class_id}_{view_id}_{other_id}"))
        builder.adjust(1)
    builder.add(types.InlineKeyboardButton(text="🔍 Показать все товары", callback_data=f"show_tech_{purpose_id}_{type_id}_{class_id}_{view_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"class_tech_{purpose_id}_{type_id}_{class_id}"))
    view_name = pview[0] if pview else "Вид"
    await callback.message.edit_text(f"📦 **{view_name}**\n\nВыберите иные характеристики или посмотрите все товары:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("show_tech_"))
async def show_tech_items(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    class_id = int(parts[4])
    view_id = int(parts[5])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT ap.id, ap.title, ap.price, u.username FROM auto_products ap JOIN users u ON ap.user_id = u.user_id WHERE ap.status = 'active' AND ap.purpose_id = ? AND ap.type_id = ? AND ap.class_id = ? AND ap.view_id = ? ORDER BY ap.created_at DESC LIMIT 20", (purpose_id, type_id, class_id, view_id))
        items = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if items:
        for item_id, title, price, username in items:
            price_text = f"{price}₽" if price else "Цена не указана"
            button_text = f"{title[:30]}... - {price_text}"
            builder.add(types.InlineKeyboardButton(text=button_text, callback_data=f"item_tech_{item_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет предложений", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_tech"))
    text = "📦 **Каталог товаров**\n\n"
    if items:
        text += f"Найдено товаров: {len(items)}\n\nВыберите интересующий вариант:"
    else:
        text += "Пока нет товаров."
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "catalog_services")
async def catalog_services(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT id, name FROM service_purposes ORDER BY id")
        purposes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if purposes:
        for purpose_id, purpose_name in purposes:
            builder.add(types.InlineKeyboardButton(text=purpose_name, callback_data=f"purpose_service_{purpose_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет категорий", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="personal_account"))
    await callback.message.edit_text("🛠 **Каталог услуг**\n\nВыберите категорию по назначению:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("purpose_service_"))
async def catalog_service_purpose(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    purpose_id = int(callback.data.split("_")[-1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_purposes WHERE id = ?", (purpose_id,))
        purpose = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM service_types ORDER BY id")
        types_list = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if types_list:
        for type_id, type_name in types_list:
            builder.add(types.InlineKeyboardButton(text=type_name, callback_data=f"type_service_{purpose_id}_{type_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет подкатегорий", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_services"))
    purpose_name = purpose[0] if purpose else "Категория"
    await callback.message.edit_text(f"🛠 **{purpose_name}**\n\nВыберите подкатегорию по типу:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("type_service_"))
async def catalog_service_type(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_types WHERE id = ?", (type_id,))
        ptype = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM service_classes ORDER BY id")
        classes = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if classes:
        for class_id, class_name in classes:
            builder.add(types.InlineKeyboardButton(text=class_name, callback_data=f"class_service_{purpose_id}_{type_id}_{class_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет классов", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"purpose_service_{purpose_id}"))
    type_name = ptype[0] if ptype else "Тип"
    await callback.message.edit_text(f"🛠 **{type_name}**\n\nВыберите класс:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("class_service_"))
async def catalog_service_class(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    class_id = int(parts[4])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_classes WHERE id = ?", (class_id,))
        pclass = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM service_views ORDER BY id")
        views = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if views:
        for view_id, view_name in views:
            builder.add(types.InlineKeyboardButton(text=view_name, callback_data=f"view_service_{purpose_id}_{type_id}_{class_id}_{view_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет видов", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"type_service_{purpose_id}_{type_id}"))
    class_name = pclass[0] if pclass else "Класс"
    await callback.message.edit_text(f"🛠 **{class_name}**\n\nВыберите вид:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("view_service_"))
async def catalog_service_view(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    class_id = int(parts[4])
    view_id = int(parts[5])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT name FROM service_views WHERE id = ?", (view_id,))
        pview = await cursor.fetchone()
        cursor = await db.execute("SELECT id, name FROM service_other_chars ORDER BY id")
        others = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if others:
        for other_id, other_name in others:
            builder.add(types.InlineKeyboardButton(text=other_name, callback_data=f"other_service_{purpose_id}_{type_id}_{class_id}_{view_id}_{other_id}"))
        builder.adjust(1)
    builder.add(types.InlineKeyboardButton(text="🔍 Показать все услуги", callback_data=f"show_service_{purpose_id}_{type_id}_{class_id}_{view_id}"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data=f"class_service_{purpose_id}_{type_id}_{class_id}"))
    view_name = pview[0] if pview else "Вид"
    await callback.message.edit_text(f"🛠 **{view_name}**\n\nВыберите иные характеристики или посмотрите все услуги:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("show_service_"))
async def show_service_items(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    parts = callback.data.split("_")
    purpose_id = int(parts[2])
    type_id = int(parts[3])
    class_id = int(parts[4])
    view_id = int(parts[5])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT as_.id, as_.title, as_.price, u.username FROM auto_services as_ JOIN users u ON as_.user_id = u.user_id WHERE as_.status = 'active' AND as_.purpose_id = ? AND as_.type_id = ? AND as_.class_id = ? AND as_.view_id = ? ORDER BY as_.created_at DESC LIMIT 20", (purpose_id, type_id, class_id, view_id))
        items = await cursor.fetchall()
    builder = InlineKeyboardBuilder()
    if items:
        for item_id, title, price, username in items:
            price_text = f"{price}₽" if price else "Цена не указана"
            button_text = f"{title[:30]}... - {price_text}"
            builder.add(types.InlineKeyboardButton(text=button_text, callback_data=f"item_service_{item_id}"))
        builder.adjust(1)
    else:
        builder.add(types.InlineKeyboardButton(text="Пока нет услуг", callback_data="empty"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="catalog_services"))
    text = "🛠 **Каталог услуг**\n\n"
    if items:
        text += f"Найдено услуг: {len(items)}\n\nВыберите интересующий вариант:"
    else:
        text += "Пока нет услуг."
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("item_tech_"))
async def show_product_details(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    item_id = int(callback.data.split("_")[-1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT ap.title, ap.description, ap.price, ap.category_id, ap.user_id, ap.contact_info, u.username, c.name FROM auto_products ap LEFT JOIN users u ON ap.user_id = u.user_id LEFT JOIN categories c ON ap.category_id = c.id WHERE ap.id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await callback.answer("Предложение не найдено", show_alert=True)
        return
    title, description, price, cat_id, user_id, contact_info, username, cat_name = item
    text = f"📦 **{title}**\n\nКатегория: {cat_name or 'Не указана'}\n"
    text += f"Цена: {price}₽\n" if price else "Цена: Не указана\n"
    text += f"\n{description}\n" if description else "\n"
    text += f"\n👤 Продавец: @{username}" if username else f"\n👤 Продавец: ID {user_id}"
    if contact_info:
        text += f"\n📞 Контакты: {contact_info}"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="catalog_tech"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("item_service_"))
async def show_service_details(callback: CallbackQuery):
    if await check_blocked_user(callback):
        return
    item_id = int(callback.data.split("_")[-1])
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT as_.title, as_.description, as_.price, as_.category_id, as_.user_id, as_.contact_info, u.username, c.name FROM auto_services as_ LEFT JOIN users u ON as_.user_id = u.user_id LEFT JOIN categories c ON as_.category_id = c.id WHERE as_.id = ?", (item_id,))
        item = await cursor.fetchone()
    if not item:
        await callback.answer("Предложение не найдено", show_alert=True)
        return
    title, description, price, cat_id, user_id, contact_info, username, cat_name = item
    text = f"🛠 **{title}**\n\nКатегория: {cat_name or 'Не указана'}\n"
    text += f"Цена: {price}₽\n" if price else "Цена: Не указана\n"
    text += f"\n{description}\n" if description else "\n"
    text += f"\n👤 Исполнитель: @{username}" if username else f"\n👤 Исполнитель: ID {user_id}"
    if contact_info:
        text += f"\n📞 Контакты: {contact_info}"
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="catalog_services"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
