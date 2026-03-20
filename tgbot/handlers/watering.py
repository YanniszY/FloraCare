from aiogram import Router, F, types

from ..api.api import water_all_plants, get_plants, water_plant
from ..keyboards.plants_inline import plant_todo_keyboard

router = Router()

@router.callback_query(F.data == "water_all")
async def handle_water_all(callback: types.CallbackQuery):
    # Здесь ты делаешь запрос к своему Бэкенду: 
    # requests.post(f"{BACKEND_URL}/api/plants/water-all/{callback.from_user.id}")


    r = water_all_plants()

    if r.status_code == 200:

        data = r.json()

        if data["updated"] == 0:
            await callback.answer("🌿 Все растения уже политы")
        else:
            await callback.answer(f"💧 Полито растений: {data['updated']}")

    else:
        await callback.answer("❌ Ошибка")
    
    await callback.message.edit_text("✅ Все растения отмечены как политые!")
    await callback.answer()




@router.callback_query(F.data == "show_todo")
async def handle_show_todo(callback: types.CallbackQuery):

    await callback.answer("Загружаю список...")

    r = get_plants()

    # if r.status_code != 200:
    #     await callback.message.answer("❌ Ошибка загрузки растений")
    #     return

    plants = r

    if not plants:
        await callback.message.answer("🌿 У вас нет растений")
        return

    for p in plants:

        if p['needs_watering']:

            text = (
                f"🌿 {p['name']}\n"
                f"📍 {p['location']}\n"
                f"💧 Последний полив: {p['last_watered']}"
            )

            await callback.message.answer(
                text,
                reply_markup=plant_todo_keyboard(p["id"])
            )




@router.callback_query(F.data.startswith("water_"))
async def handle_water(callback: types.CallbackQuery):

    plant_id = int(callback.data.split("_")[1])

    r = water_plant(plant_id)

    if r.status_code == 200:
        await callback.answer("💧 Полито!")
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Полито"
        )
    else:
        await callback.answer("❌ Ошибка")