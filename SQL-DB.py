import sys
import mysql.connector
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, 
                             QMessageBox, QGroupBox, QTabWidget, QTreeWidget, 
                             QTreeWidgetItem, QFormLayout, QScrollArea)

class SQLManagerProject(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = None 
        self.dynamic_inputs = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("SQL Manager Express - Gestion Complète")
        self.resize(950, 850)
        main_layout = QVBoxLayout()

        # --- CONNEXION ---
        conn_group = QGroupBox("Connexion Serveur (Docker)")
        conn_grid = QHBoxLayout()
        self.host = QLineEdit("ip_mysql_server")
        self.user = QLineEdit("name_user")
        self.password = QLineEdit("password_user")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.btn_connect = QPushButton("Connecter")
        self.btn_connect.clicked.connect(self.connect_server)
        self.btn_disconnect = QPushButton("Déconnecter")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self.disconnect_server)
        for w in [self.host, self.user, self.password, self.btn_connect, self.btn_disconnect]: conn_grid.addWidget(w)
        conn_group.setLayout(conn_grid)
        main_layout.addWidget(conn_group)

        # --- ONGLETS ---
        self.tabs = QTabWidget()
        self.tabs.setEnabled(False)
        
        # 1. STRUCTURE (Création & Modification)
        self.tab_structure = QWidget()
        self.init_structure_tab()
        self.tabs.addTab(self.tab_structure, "🛠 Structure")

        # 2. INSERTION
        self.tab_insert = QWidget()
        self.init_insert_tab()
        self.tabs.addTab(self.tab_insert, "📥 Insertion")

        # 3. EXPLORATEUR
        self.tab_data = QWidget()
        self.init_data_tab()
        self.tabs.addTab(self.tab_data, "👁 Explorateur")

        main_layout.addWidget(self.tabs)

        self.log_area = QTextEdit()
        self.log_area.setFixedHeight(120)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: Consolas;")
        main_layout.addWidget(self.log_area)

        self.setLayout(main_layout)

    def init_structure_tab(self):
        layout = QVBoxLayout()
        
        # --- SECTION : CRÉER DB ---
        db_group = QGroupBox("Bases de Données")
        db_lay = QHBoxLayout()
        self.new_db_name = QLineEdit()
        self.new_db_name.setPlaceholderText("Nom de la DB")
        btn_create_db = QPushButton("Créer la DB")
        btn_create_db.clicked.connect(self.create_database)
        db_lay.addWidget(self.new_db_name); db_lay.addWidget(btn_create_db)
        db_group.setLayout(db_lay)
        
        # --- SECTION : CRÉER TABLE ---
        table_group = QGroupBox("Créer une nouvelle Table")
        t_lay = QVBoxLayout()
        self.target_db = QLineEdit(); self.target_db.setPlaceholderText("Nom de la base")
        self.new_table_name = QLineEdit(); self.new_table_name.setPlaceholderText("Nom de la table")
        h_col = QHBoxLayout()
        self.col_name = QLineEdit(); self.col_name.setPlaceholderText("Première colonne")
        self.col_type = QComboBox()
        self.col_type.addItems(["INT PRIMARY KEY AUTO_INCREMENT", "VARCHAR(255)", "TEXT", "DATETIME", "INT"])
        h_col.addWidget(self.col_name); h_col.addWidget(self.col_type)
        btn_create_t = QPushButton("Créer la Table")
        btn_create_t.clicked.connect(self.create_table)
        t_lay.addWidget(self.target_db); t_lay.addWidget(self.new_table_name); t_lay.addLayout(h_col); t_lay.addWidget(btn_create_t)
        table_group.setLayout(t_lay)

        # --- SECTION : AJOUTER COLONNE (NOUVEAU) ---
        alter_group = QGroupBox("Ajouter une Colonne à une table existante")
        a_lay = QVBoxLayout()
        h_target = QHBoxLayout()
        self.alter_db = QLineEdit(); self.alter_db.setPlaceholderText("Base cible")
        self.alter_table = QLineEdit(); self.alter_table.setPlaceholderText("Table cible")
        h_target.addWidget(self.alter_db); h_target.addWidget(self.alter_table)
        
        h_new_col = QHBoxLayout()
        self.add_col_name = QLineEdit(); self.add_col_name.setPlaceholderText("Nom nouvelle colonne")
        self.add_col_type = QComboBox()
        self.add_col_type.addItems(["VARCHAR(255)", "TEXT", "INT", "DATETIME", "DECIMAL(10,2)"])
        h_new_col.addWidget(self.add_col_name); h_new_col.addWidget(self.add_col_type)
        
        btn_add_col = QPushButton("Ajouter la colonne")
        btn_add_col.setStyleSheet("background-color: #3498db; color: white;")
        btn_add_col.clicked.connect(self.add_column_to_table)
        
        a_lay.addLayout(h_target); a_lay.addLayout(h_new_col); a_lay.addWidget(btn_add_col)
        alter_group.setLayout(a_lay)

        layout.addWidget(db_group); layout.addWidget(table_group); layout.addWidget(alter_group); layout.addStretch()
        self.tab_structure.setLayout(layout)

    # --- LOGIQUE DE CONNEXION ---
    def connect_server(self):
        try:
            self.conn = mysql.connector.connect(host=self.host.text(), user=self.user.text(), password=self.password.text(), auth_plugin='mysql_native_password')
            self.log_area.append("✅ Connecté"); self.tabs.setEnabled(True); self.btn_connect.setEnabled(False); self.btn_disconnect.setEnabled(True); self.refresh_explorer()
        except Exception as e: QMessageBox.critical(self, "Erreur", str(e))

    def disconnect_server(self):
        if self.conn: self.conn.close(); self.conn = None
        self.log_area.append("🔌 Déconnecté"); self.tabs.setEnabled(False); self.btn_connect.setEnabled(True); self.btn_disconnect.setEnabled(False); self.tree.clear()

    # --- ACTIONS SQL ---
    def create_database(self):
        try:
            cur = self.conn.cursor(); cur.execute(f"CREATE DATABASE {self.new_db_name.text()}")
            self.log_area.append(f"✅ DB '{self.new_db_name.text()}' créée."); self.refresh_explorer()
        except Exception as e: self.log_area.append(f"❌ {e}")

    def create_table(self):
        try:
            cur = self.conn.cursor()
            cur.execute(f"USE {self.target_db.text()}")
            sql = f"CREATE TABLE {self.new_table_name.text()} ({self.col_name.text()} {self.col_type.currentText()})"
            cur.execute(sql)
            self.log_area.append(f"✅ Table '{self.new_table_name.text()}' créée."); self.refresh_explorer()
        except Exception as e: self.log_area.append(f"❌ {e}")

    def add_column_to_table(self):
        """Fonction pour ajouter une colonne avec ALTER TABLE"""
        db = self.alter_db.text(); table = self.alter_table.text()
        col = self.add_col_name.text(); dtype = self.add_col_type.currentText()
        if not all([db, table, col]): return
        try:
            cur = self.conn.cursor()
            sql = f"ALTER TABLE {db}.{table} ADD {col} {dtype}"
            cur.execute(sql)
            self.conn.commit()
            self.log_area.append(f"✅ Colonne '{col}' ajoutée à {table}")
        except Exception as e: QMessageBox.warning(self, "Erreur SQL", str(e))

    def load_columns_for_insert(self):
        db = self.ins_db.text(); table = self.ins_table.text()
        if not db or not table: return
        try:
            while self.form_layout.count():
                item = self.form_layout.takeAt(0); (item.widget().deleteLater() if item.widget() else None)
            self.dynamic_inputs = {}
            cur = self.conn.cursor(); cur.execute(f"DESCRIBE {db}.{table}")
            for col in cur.fetchall():
                if "auto_increment" in col[5].lower(): continue
                inp = QLineEdit(); self.form_layout.addRow(f"{col[0]}:", inp); self.dynamic_inputs[col[0]] = inp
            self.btn_confirm_insert.setEnabled(True)
        except Exception as e: QMessageBox.warning(self, "Erreur", str(e))

    def execute_insertion(self):
        db = self.ins_db.text(); table = self.ins_table.text()
        cols = ", ".join(self.dynamic_inputs.keys()); placeholders = ", ".join(["%s"] * len(self.dynamic_inputs))
        values = [i.text() for i in self.dynamic_inputs.values()]
        try:
            cur = self.conn.cursor(); cur.execute(f"USE {db}")
            cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
            self.conn.commit(); self.log_area.append("📥 Données insérées"); [i.clear() for i in self.dynamic_inputs.values()]
        except Exception as e: QMessageBox.critical(self, "Erreur", str(e))

    def refresh_explorer(self):
        if not self.conn: return
        self.tree.clear()
        try:
            cur = self.conn.cursor(); cur.execute("SHOW DATABASES")
            for (db,) in cur.fetchall():
                if db in ['sys', 'performance_schema', 'mysql', 'information_schema']: continue
                dbi = QTreeWidgetItem([db, "DB"]); self.tree.addTopLevelItem(dbi)
                c2 = self.conn.cursor(); c2.execute(f"SHOW TABLES FROM {db}")
                for (t,) in c2.fetchall(): dbi.addChild(QTreeWidgetItem([t, "Table"]))
        except Exception as e: self.log_area.append(str(e))

    def delete_item(self):
        item = self.tree.currentItem()
        if not item: return
        try:
            cur = self.conn.cursor()
            if item.parent(): cur.execute(f"DROP TABLE {item.parent().text(0)}.{item.text(0)}")
            else: cur.execute(f"DROP DATABASE {item.text(0)}")
            self.refresh_explorer()
        except Exception as e: QMessageBox.critical(self, "Erreur", str(e))

    def init_insert_tab(self):
        layout = QVBoxLayout()
        sel_group = QGroupBox("Cible"); sel_lay = QHBoxLayout()
        self.ins_db = QLineEdit(); self.ins_db.setPlaceholderText("Base")
        self.ins_table = QLineEdit(); self.ins_table.setPlaceholderText("Table")
        btn_load = QPushButton("Charger colonnes"); btn_load.clicked.connect(self.load_columns_for_insert)
        sel_lay.addWidget(self.ins_db); sel_lay.addWidget(self.ins_table); sel_lay.addWidget(btn_load)
        sel_group.setLayout(sel_lay); layout.addWidget(sel_group)
        self.scroll = QScrollArea(); self.scroll_content = QWidget(); self.form_layout = QFormLayout()
        self.scroll_content.setLayout(self.form_layout); self.scroll.setWidgetResizable(True); self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        self.btn_confirm_insert = QPushButton("Insérer"); self.btn_confirm_insert.setEnabled(False); self.btn_confirm_insert.clicked.connect(self.execute_insertion)
        layout.addWidget(self.btn_confirm_insert); self.tab_insert.setLayout(layout)

    def init_data_tab(self):
        layout = QVBoxLayout()
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(["Nom", "Type"])
        btn_refresh = QPushButton("Actualiser"); btn_refresh.clicked.connect(self.refresh_explorer)
        btn_delete = QPushButton("Supprimer"); btn_delete.clicked.connect(self.delete_item)
        layout.addWidget(btn_refresh); layout.addWidget(self.tree); layout.addWidget(btn_delete)
        self.tab_data.setLayout(layout)

    def closeEvent(self, event):
        if self.conn: self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SQLManagerProject()
    window.show()
    sys.exit(app.exec())