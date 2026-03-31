"""
Скрипт миграции для удаления неиспользуемых полей из базы данных

Удаляет следующие поля:
- users.is_verified
- teas.is_seasonal
- teas.season
- ingredients.is_popular
- ingredients.usage_count
- reviews.helpful_count

Также удаляет таблицу articles, если она существует.
"""
import asyncio
import sqlite3
from pathlib import Path


async def run_migration():
    """Выполняет миграцию для удаления неиспользуемых полей"""
    
    # Путь к базе данных
    db_path = Path(__file__).parent.parent / "db.sqlite3"
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    print(f"📦 Подключение к базе данных: {db_path}")
    
    # Используем синхронное подключение для SQLite
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Проверяем существование таблиц и колонок перед удалением
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Найдено таблиц: {len(tables)}")
        
        # Список используемых таблиц (из моделей TortoiseORM)
        used_tables = {
            'users', 'countries', 'regions', 'tea_types', 'tea_flavors', 'teas',
            'ingredient_categories', 'ingredients', 'custom_blends', 'blend_components',
            'orders', 'order_items', 'reviews',
            # Системные таблицы SQLite
            'sqlite_sequence', 'sqlite_master', 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4'
        }
        
        # Находим неиспользуемые таблицы
        unused_tables = [t for t in tables if t not in used_tables]
        
        if unused_tables:
            print(f"\n🗑️  Найдено неиспользуемых таблиц: {len(unused_tables)}")
            for table in unused_tables:
                print(f"  → {table}")
            
            # Удаляем неиспользуемые таблицы
            for table in unused_tables:
                print(f"\n🗑️  Удаление таблицы {table}...")
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Таблица {table} удалена")
        else:
            print("\nℹ️  Неиспользуемые таблицы не найдены")
        
        # SQLite не поддерживает ALTER TABLE DROP COLUMN напрямую
        # Нужно создать новую таблицу без колонок и скопировать данные
        
        # 1. Удаление is_verified из users
        if 'users' in tables:
            print("\n🔄 Обработка таблицы users...")
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_verified' in columns:
                print("  → Удаление колонки is_verified...")
                # Создаем временную таблицу без is_verified
                cursor.execute("""
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        username VARCHAR(100) NOT NULL UNIQUE,
                        hashed_password VARCHAR(255) NOT NULL,
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        phone VARCHAR(20),
                        role INTEGER NOT NULL DEFAULT 1,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        address TEXT,
                        city VARCHAR(100),
                        postal_code VARCHAR(20),
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        last_login TIMESTAMP
                    )
                """)
                
                # Копируем данные (без is_verified)
                cursor.execute("""
                    INSERT INTO users_new 
                    (id, email, username, hashed_password, first_name, last_name, phone, 
                     role, is_active, address, city, postal_code, created_at, updated_at, last_login)
                    SELECT 
                    id, email, username, hashed_password, first_name, last_name, phone,
                    role, is_active, address, city, postal_code, created_at, updated_at, last_login
                    FROM users
                """)
                
                # Удаляем старую таблицу и переименовываем новую
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")
                print("  ✅ Колонка is_verified удалена")
            else:
                print("  ℹ️  Колонка is_verified не найдена, пропускаем")
        
        # 2. Удаление is_seasonal и season из teas
        if 'teas' in tables:
            print("\n🔄 Обработка таблицы teas...")
            cursor.execute("PRAGMA table_info(teas)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_seasonal' in columns or 'season' in columns:
                print("  → Удаление колонок is_seasonal и season...")
                # Получаем все колонки кроме удаляемых
                cursor.execute("PRAGMA table_info(teas)")
                all_columns = cursor.fetchall()
                keep_columns = [col[1] for col in all_columns 
                               if col[1] not in ['is_seasonal', 'season']]
                
                # Создаем SQL для создания новой таблицы
                # Нужно получить полную структуру из модели или использовать более простой подход
                # Для SQLite проще всего пересоздать таблицу
                cursor.execute("""
                    CREATE TABLE teas_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(200) NOT NULL,
                        name_en VARCHAR(200),
                        slug VARCHAR(250) NOT NULL UNIQUE,
                        country_id INTEGER,
                        region_id INTEGER,
                        tea_type_id INTEGER NOT NULL,
                        description TEXT,
                        short_description VARCHAR(500),
                        price_per_100g DECIMAL(10,2) NOT NULL,
                        price_per_20g DECIMAL(10,2),
                        stock_quantity INTEGER NOT NULL DEFAULT 0,
                        is_available INTEGER NOT NULL DEFAULT 1,
                        rating REAL NOT NULL DEFAULT 0.0,
                        review_count INTEGER NOT NULL DEFAULT 0,
                        purchase_count INTEGER NOT NULL DEFAULT 0,
                        main_image_url VARCHAR(500),
                        image_urls TEXT NOT NULL DEFAULT '[]',
                        is_featured INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (country_id) REFERENCES countries(id),
                        FOREIGN KEY (region_id) REFERENCES regions(id),
                        FOREIGN KEY (tea_type_id) REFERENCES tea_types(id)
                    )
                """)
                
                # Копируем данные
                cursor.execute("""
                    INSERT INTO teas_new 
                    (id, name, name_en, slug, country_id, region_id, tea_type_id, description,
                     short_description, price_per_100g, price_per_20g, stock_quantity, is_available,
                     rating, review_count, purchase_count, main_image_url, image_urls, is_featured,
                     created_at, updated_at)
                    SELECT 
                    id, name, name_en, slug, country_id, region_id, tea_type_id, description,
                    short_description, price_per_100g, price_per_20g, stock_quantity, is_available,
                    rating, review_count, purchase_count, main_image_url, image_urls, is_featured,
                    created_at, updated_at
                    FROM teas
                """)
                
                # Удаляем старую таблицу и переименовываем новую
                cursor.execute("DROP TABLE teas")
                cursor.execute("ALTER TABLE teas_new RENAME TO teas")
                print("  ✅ Колонки is_seasonal и season удалены")
            else:
                print("  ℹ️  Колонки is_seasonal и season не найдены, пропускаем")
        
        # 3. Удаление is_popular и usage_count из ingredients
        if 'ingredients' in tables:
            print("\n🔄 Обработка таблицы ingredients...")
            cursor.execute("PRAGMA table_info(ingredients)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'is_popular' in columns or 'usage_count' in columns:
                print("  → Удаление колонок is_popular и usage_count...")
                cursor.execute("""
                    CREATE TABLE ingredients_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        name_en VARCHAR(100),
                        description TEXT,
                        category_id INTEGER NOT NULL,
                        price_per_100g DECIMAL(10,2) NOT NULL,
                        price_per_20g DECIMAL(10,2),
                        stock_quantity INTEGER NOT NULL DEFAULT 0,
                        is_available INTEGER NOT NULL DEFAULT 1,
                        flavor_profile VARCHAR(200),
                        image_url VARCHAR(500),
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (category_id) REFERENCES ingredient_categories(id)
                    )
                """)
                
                # Копируем данные
                cursor.execute("""
                    INSERT INTO ingredients_new 
                    (id, name, name_en, description, category_id, price_per_100g, price_per_20g,
                     stock_quantity, is_available, flavor_profile, image_url, created_at, updated_at)
                    SELECT 
                    id, name, name_en, description, category_id, price_per_100g, price_per_20g,
                    stock_quantity, is_available, flavor_profile, image_url, created_at, updated_at
                    FROM ingredients
                """)
                
                cursor.execute("DROP TABLE ingredients")
                cursor.execute("ALTER TABLE ingredients_new RENAME TO ingredients")
                print("  ✅ Колонки is_popular и usage_count удалены")
            else:
                print("  ℹ️  Колонки is_popular и usage_count не найдены, пропускаем")
        
        # 4. Удаление helpful_count из reviews
        if 'reviews' in tables:
            print("\n🔄 Обработка таблицы reviews...")
            cursor.execute("PRAGMA table_info(reviews)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'helpful_count' in columns:
                print("  → Удаление колонки helpful_count...")
                cursor.execute("""
                    CREATE TABLE reviews_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        tea_id INTEGER,
                        custom_blend_id INTEGER,
                        rating INTEGER NOT NULL,
                        title VARCHAR(200),
                        text TEXT,
                        is_approved INTEGER NOT NULL DEFAULT 1,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (tea_id) REFERENCES teas(id),
                        FOREIGN KEY (custom_blend_id) REFERENCES custom_blends(id),
                        UNIQUE(user_id, tea_id),
                        UNIQUE(user_id, custom_blend_id)
                    )
                """)
                
                # Копируем данные
                cursor.execute("""
                    INSERT INTO reviews_new 
                    (id, user_id, tea_id, custom_blend_id, rating, title, text, is_approved,
                     created_at, updated_at)
                    SELECT 
                    id, user_id, tea_id, custom_blend_id, rating, title, text, is_approved,
                    created_at, updated_at
                    FROM reviews
                """)
                
                cursor.execute("DROP TABLE reviews")
                cursor.execute("ALTER TABLE reviews_new RENAME TO reviews")
                print("  ✅ Колонка helpful_count удалена")
            else:
                print("  ℹ️  Колонка helpful_count не найдена, пропускаем")
        
        # Сохраняем изменения
        conn.commit()
        print("\n✅ Миграция успешно завершена!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Ошибка при выполнении миграции: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 Запуск миграции для удаления неиспользуемых полей...\n")
    asyncio.run(run_migration())

