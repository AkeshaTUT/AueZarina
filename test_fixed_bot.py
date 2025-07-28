"""
Тест исправленного бота - проверяем показ всех скидок
"""
import asyncio
from steam_scraper import SteamScraper

async def test_all_deals():
    """Тестирует показ всех найденных скидок"""
    print("🔍 Тестирование показа всех скидок...")
    
    scraper = SteamScraper()
    deals = await scraper.get_discounted_games(min_discount=30, max_results=100)
    
    print(f"📊 Всего найдено скидок: {len(deals)}")
    print("🎮 Топ-10 скидок:")
    
    for i, deal in enumerate(deals[:10], 1):
        print(f"{i:2d}. {deal['title']} (-{deal['discount']}%)")
    
    if len(deals) > 10:
        print(f"... и еще {len(deals) - 10} скидок")
    
    # Тестируем разбивку сообщений
    from steam_bot import SteamDiscountBot
    
    class MockBot:
        def format_deals_message(self, deals):
            if not deals:
                return "Нет скидок"
            
            message = f"🎮 Актуальные скидки Steam ({len(deals)} игр)\n\n"
            for deal in deals:
                message += f"💥 {deal['title']} (-{deal['discount']}%)\n"
                message += f"🔗 {deal['url']}\n\n"
            return message
        
        def split_message(self, message, max_length):
            chunks = []
            current_chunk = ""
            
            for line in message.split('\n'):
                if len(current_chunk + line + '\n') > max_length:
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = line + '\n'
                    else:
                        chunks.append(line)
                else:
                    current_chunk += line + '\n'
            
            if current_chunk:
                chunks.append(current_chunk)
                
            return chunks
    
    mock_bot = MockBot()
    message = mock_bot.format_deals_message(deals)
    
    print(f"\n📏 Длина сообщения: {len(message)} символов")
    
    if len(message) > 4000:
        chunks = mock_bot.split_message(message, 4000)
        print(f"📨 Сообщение разбито на {len(chunks)} частей:")
        for i, chunk in enumerate(chunks, 1):
            print(f"  Часть {i}: {len(chunk)} символов")
    else:
        print("✅ Сообщение помещается в один блок")

if __name__ == "__main__":
    asyncio.run(test_all_deals())
