import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import threading
import json
import os
from datetime import datetime
from agente_transparencia import AgenteTransparencia
from agente_contactos import AgenteContactos
from coordinador import Coordinador

# Configurar tema
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class TransparenciaContactosApp:
    def __init__(self):
        # Colores de Amazon
        self.colors = {
            'primary': '#FF9900',
            'secondary': '#232F3E',
            'background': '#FFFFFF',
            'text': '#0F1111',
            'accent': '#FF8C00',
            'light_gray': '#F7F8F8',
            'dark_gray': '#565959',
            'success': '#067D62',
            'error': '#D13212'
        }
        
        self.setup_window()
        self.coordinador = Coordinador()
        self.resultados = []
        self.setup_ui()
        
    def setup_window(self):
        """Configurar ventana principal"""
        self.root = ctk.CTk()
        self.root.title("🕵️ Investigador de Entidades - Transparencia & Contactos")
        self.root.geometry("1200x800")
        self.root.configure(fg_color=self.colors['background'])
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Frame principal
        main_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.colors['background'],
            corner_radius=0
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(
            main_frame,
            fg_color=self.colors['secondary'],
            corner_radius=10,
            height=120
        )
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🕵️ Investigador de Entidades",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=(15, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Filtra contactos estratégicos para adquisición de servicios AWS",
            font=ctk.CTkFont(size=16),
            text_color="#CCCCCC"
        )
        subtitle_label.pack()
        
        info_label = ctk.CTkLabel(
            header_frame,
            text="Identifica directores de tecnología, administración, finanzas e innovación",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        info_label.pack(pady=(5, 0))
        
        # Contenedor principal
        content_frame = ctk.CTkFrame(
            main_frame,
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True)
        
        # Panel izquierdo - Entrada
        left_panel = ctk.CTkFrame(
            content_frame,
            fg_color=self.colors['light_gray'],
            corner_radius=10
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Instrucciones
        instructions_label = ctk.CTkLabel(
            left_panel,
            text="📝 Ingrese las entidades a investigar:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['text']
        )
        instructions_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        info_label = ctk.CTkLabel(
            left_panel,
            text="🎯 Filtra contactos relevantes para adquisición de servicios AWS:\n• Directores de Tecnología, Administración, Finanzas e Innovación\n• Coordinadores y Jefes de áreas estratégicas",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['dark_gray'],
            justify="left"
        )
        info_label.pack(pady=(0, 15), padx=20, anchor="w")
        
        # Cuadro de texto
        self.text_entidades = ctk.CTkTextbox(
            left_panel,
            height=200,
            font=ctk.CTkFont(size=14),
            fg_color="white",
            text_color=self.colors['text'],
            border_color=self.colors['primary'],
            border_width=2,
            corner_radius=8
        )
        self.text_entidades.pack(fill="x", padx=20, pady=(0, 20))
        
        # Placeholder
        placeholder_text = """Ejemplo:
Secretaría de Educación Pública
Instituto Nacional Electoral
Comisión Nacional de Derechos Humanos
Secretaría de Salud"""
        
        self.text_entidades.insert("1.0", placeholder_text)
        self.text_entidades.configure(text_color=self.colors['dark_gray'])
        self.text_entidades.bind("<FocusIn>", self.clear_placeholder)
        self.text_entidades.bind("<FocusOut>", self.add_placeholder)
        self.is_placeholder = True
        
        # Botones
        buttons_frame = ctk.CTkFrame(
            left_panel,
            fg_color="transparent"
        )
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_investigar = ctk.CTkButton(
            buttons_frame,
            text="🚀 Iniciar Investigación AWS",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=self.colors['primary'],
            hover_color=self.colors['accent'],
            text_color="white",
            height=50,
            corner_radius=25,
            command=self.iniciar_investigacion
        )
        self.btn_investigar.pack(pady=(0, 10))
        
        # Frame para resultados AWS
        self.frame_resultados = ctk.CTkScrollableFrame(
            left_panel,
            height=300,
            fg_color="white",
            corner_radius=8,
            border_color=self.colors['primary'],
            border_width=1
        )
        self.frame_resultados.pack(fill="x", padx=20, pady=(10, 0))
        
        self.btn_descargar = ctk.CTkButton(
            buttons_frame,
            text="💾 Descargar Excel AWS",
            font=ctk.CTkFont(size=14),
            fg_color=self.colors['success'],
            hover_color="#045D4A",
            text_color="white",
            height=40,
            corner_radius=20,
            command=self.descargar_excel_aws,
            state="disabled"
        )
        self.btn_descargar.pack()
        
        # Variable para almacenar resultados
        self.resultados_aws = None
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            left_panel,
            progress_color=self.colors['primary'],
            fg_color=self.colors['light_gray'],
            height=8,
            corner_radius=4
        )
        self.progress.pack(fill="x", padx=20, pady=(10, 20))
        self.progress.set(0)
        
        # Panel derecho - Log
        right_panel = ctk.CTkFrame(
            content_frame,
            fg_color=self.colors['light_gray'],
            corner_radius=10
        )
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        log_title = ctk.CTkLabel(
            right_panel,
            text="📋 Log de Investigación en Tiempo Real:",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['text']
        )
        log_title.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Área de log
        self.text_log = ctk.CTkTextbox(
            right_panel,
            font=ctk.CTkFont(size=11),
            fg_color="white",
            text_color=self.colors['text'],
            border_color=self.colors['dark_gray'],
            border_width=1,
            corner_radius=8
        )
        self.text_log.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Status bar
        self.status_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.colors['secondary'],
            height=30,
            corner_radius=0
        )
        self.status_frame.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="✅ Sistema listo - Ambos agentes preparados",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        self.status_label.pack(pady=5)
        
    def clear_placeholder(self, event=None):
        """Limpiar placeholder"""
        if self.is_placeholder:
            self.text_entidades.delete("1.0", "end")
            self.text_entidades.configure(text_color=self.colors['text'])
            self.is_placeholder = False
            
    def add_placeholder(self, event=None):
        """Agregar placeholder si está vacío"""
        if not self.text_entidades.get("1.0", "end").strip():
            placeholder_text = """Ejemplo:
Secretaría de Educación Pública
Instituto Nacional Electoral
Comisión Nacional de Derechos Humanos
Secretaría de Salud"""
            self.text_entidades.insert("1.0", placeholder_text)
            self.text_entidades.configure(text_color=self.colors['dark_gray'])
            self.is_placeholder = True
    
    def log_message(self, message, tipo="info"):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if tipo == "info":
            icon = "ℹ️"
        elif tipo == "success":
            icon = "✅"
        elif tipo == "error":
            icon = "❌"
        elif tipo == "warning":
            icon = "⚠️"
        elif tipo == "download":
            icon = "📥"
        elif tipo == "search":
            icon = "🔍"
        else:
            icon = "📝"
            
        formatted_message = f"[{timestamp}] {icon} {message}\n"
        self.text_log.insert("end", formatted_message)
        self.text_log.see("end")
        self.root.update()
        
    def update_status(self, message):
        """Actualizar barra de estado"""
        self.status_label.configure(text=message)
        self.root.update()
        
    def iniciar_investigacion(self):
        """Iniciar investigación con filtrado AWS"""
        if self.is_placeholder:
            messagebox.showwarning("⚠️ Advertencia", "Por favor ingrese las entidades que desea investigar")
            return
            
        entidades_input = self.text_entidades.get("1.0", "end").strip()
        if not entidades_input:
            messagebox.showwarning("⚠️ Advertencia", "Por favor ingrese al menos una entidad")
            return
        
        # Limpiar resultados anteriores
        self.limpiar_resultados()
        
        self.btn_investigar.configure(state="disabled", text="🔎 Investigando...")
        self.btn_descargar.configure(state="disabled")
        self.progress.set(0)
        
        def investigar_thread():
            try:
                self.log_message("🚀 Iniciando investigación AWS", "info")
                self.update_status("🔍 Investigación en progreso...")
                
                # Usar el nuevo método del coordinador
                resultado = self.coordinador.investigar_multiples_entidades(entidades_input, self.log_message)
                
                if resultado.get('exito'):
                    self.resultados_aws = resultado
                    
                    # Mostrar resultados en la interfaz
                    self.mostrar_resultados_aws(resultado)
                    
                    # Habilitar botón de descarga
                    self.btn_descargar.configure(state="normal")
                    
                    self.update_status("✅ Investigación completada - Contactos AWS listos")
                    
                    total_contactos = len(resultado.get('contactos_aws', []))
                    messagebox.showinfo("🎉 Completado", 
                                      f"¡Investigación AWS completada!\n\n"
                                      f"🎯 Contactos AWS encontrados: {total_contactos}\n"
                                      f"💾 Listo para descargar Excel")
                else:
                    self.log_message(f"💥 Error: {resultado.get('error', 'Error desconocido')}", "error")
                    
            except Exception as e:
                self.log_message(f"💥 Error crítico: {str(e)}", "error")
                self.update_status("❌ Error en la investigación")
                messagebox.showerror("Error", f"Error durante la investigación:\n{str(e)}")
            finally:
                self.btn_investigar.configure(state="normal", text="🚀 Iniciar Investigación AWS")
                
        threading.Thread(target=investigar_thread, daemon=True).start()
    
    def limpiar_resultados(self):
        """Limpia los resultados anteriores"""
        for widget in self.frame_resultados.winfo_children():
            widget.destroy()
    
    def mostrar_resultados_aws(self, resultado):
        """Muestra los contactos AWS filtrados en la interfaz"""
        contactos_por_entidad = resultado.get('contactos_por_entidad', {})
        
        if not contactos_por_entidad:
            label_sin_resultados = ctk.CTkLabel(
                self.frame_resultados,
                text="⚠️ No se encontraron contactos relevantes para AWS",
                font=ctk.CTkFont(size=14),
                text_color=self.colors['error']
            )
            label_sin_resultados.pack(pady=20)
            return
        
        # Título
        titulo = ctk.CTkLabel(
            self.frame_resultados,
            text=f"🎯 Contactos AWS ({len(resultado.get('contactos_aws', []))} total)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['primary']
        )
        titulo.pack(pady=(10, 15))
        
        # Mostrar por entidad
        for entidad, contactos in contactos_por_entidad.items():
            # Frame para cada entidad
            frame_entidad = ctk.CTkFrame(
                self.frame_resultados,
                fg_color=self.colors['light_gray'],
                corner_radius=5
            )
            frame_entidad.pack(fill="x", padx=5, pady=3)
            
            # Título de entidad
            titulo_entidad = ctk.CTkLabel(
                frame_entidad,
                text=f"🏢 {entidad} ({len(contactos)} contactos)",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.colors['secondary']
            )
            titulo_entidad.pack(pady=(8, 5), padx=10, anchor="w")
            
            # Mostrar primeros 3 contactos
            for contacto in contactos[:3]:
                info_contacto = f"👤 {contacto['nombre']} | 💼 {contacto['cargo']}\n📧 {contacto['email']} | 📞 {contacto['telefono']}"
                
                label_contacto = ctk.CTkLabel(
                    frame_entidad,
                    text=info_contacto,
                    font=ctk.CTkFont(size=11),
                    justify="left",
                    anchor="w"
                )
                label_contacto.pack(pady=2, padx=15, anchor="w")
                
                # Relevancia
                relevancia = contacto.get('relevancia_aws', 0)
                color_relevancia = self.colors['success'] if relevancia >= 80 else self.colors['primary'] if relevancia >= 60 else self.colors['error']
                
                label_relevancia = ctk.CTkLabel(
                    frame_entidad,
                    text=f"🎯 {relevancia}%",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=color_relevancia
                )
                label_relevancia.pack(pady=(0, 5), padx=15, anchor="e")
            
            # Si hay más contactos
            if len(contactos) > 3:
                label_mas = ctk.CTkLabel(
                    frame_entidad,
                    text=f"... y {len(contactos) - 3} contactos más",
                    font=ctk.CTkFont(size=10, style="italic"),
                    text_color=self.colors['dark_gray']
                )
                label_mas.pack(pady=(0, 8), padx=15)
    
    def descargar_excel_aws(self):
        """Descarga el Excel con contactos AWS"""
        if not self.resultados_aws:
            messagebox.showwarning("Advertencia", "No hay resultados AWS para descargar")
            return
        
        try:
            # Crear carpeta de descarga
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            carpeta_descarga = os.path.join(os.path.expanduser("~/Downloads"), f"AWS_Contactos_{timestamp}")
            os.makedirs(carpeta_descarga, exist_ok=True)
            
            # Generar Excel
            archivo_excel = self.coordinador.generar_excel_aws(
                self.resultados_aws['contactos_por_entidad'],
                carpeta_descarga
            )
            
            self.log_message(f"💾 Excel AWS generado: {os.path.basename(archivo_excel)}", "success")
            
            # Abrir carpeta
            if os.name == 'nt':  # Windows
                os.startfile(carpeta_descarga)
            
            messagebox.showinfo("Descarga Completa", 
                              f"Excel AWS generado exitosamente:\n\n"
                              f"📁 Carpeta: {carpeta_descarga}\n"
                              f"💾 Archivo: {os.path.basename(archivo_excel)}")
                
        except Exception as e:
            self.log_message(f"Error generando Excel: {str(e)}", "error")
            messagebox.showerror("Error", f"Error al generar Excel:\n{str(e)}")
    
    def run(self):
        """Ejecutar la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TransparenciaContactosApp()
    app.run()