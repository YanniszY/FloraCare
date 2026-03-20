def dashboard_text(data):


    if data == "{'detail': 'Not Found'}":
        return "У вас нет Растений!"
    else:
        return (
            f"📊 <b>FloraCare Dashboard</b>\n\n"
            f"🌿 Растений: <b>{data['total_plants']}</b>\n"
            f"💧 Нужно полить: <b>{data['needs_watering']}</b>\n"
            f"✅ Полито сегодня: <b>{data['watered_today']}</b>\n"
            f"📅 Следующий полив: <b>{data['next_watering']}</b>"
        )



