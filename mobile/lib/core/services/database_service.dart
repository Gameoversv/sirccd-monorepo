import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

abstract interface class DatabaseService {
  Future<Database> get database;
}

final class DatabaseServiceImpl implements DatabaseService {
  Database? _db;

  @override
  Future<Database> get database async {
    _db ??= await _init();
    return _db!;
  }

  Future<Database> _init() async {
    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, 'sirccd.db');
    return openDatabase(
      path,
      version: 2,
      onCreate: (db, _) async {
        await db.execute('''
          CREATE TABLE pending_reports (
            local_id    TEXT PRIMARY KEY,
            image_path  TEXT NOT NULL,
            latitude    REAL NOT NULL,
            longitude   REAL NOT NULL,
            description TEXT,
            address     TEXT,
            city        TEXT,
            province    TEXT,
            focal_scale_factor REAL,
            sync_status TEXT NOT NULL DEFAULT 'pending',
            server_id   INTEGER,
            sync_error  TEXT,
            created_at  TEXT NOT NULL
          )
        ''');
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute(
            'ALTER TABLE pending_reports ADD COLUMN focal_scale_factor REAL',
          );
        }
      },
    );
  }
}
