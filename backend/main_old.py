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
            text="Agente 1: Descarga Excel Directorio Transparencia | Agente 2: Contactos Web",
            font=ctk.CTkFont(size=16),
            text_color="#CCCCCC"
        )
        subtitle_label.pack()
        
        info_label = ctk.CTkLabel(
            header_frame,
            text="Ambos agentes trabajan en paralelo para obtener información completa",
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
            text="🤖 Agente 1: Valida nombres → Descarga Excel directorio (Transparencia)\n🌐 Agente 2: Busca página oficial → Extrae contactos adicionales",
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
            text="🚀 Iniciar Investigación Dual",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=self.colors['primary'],
            hover_color=self.colors['accent'],
            text_color="white",
            height=50,
            corner_radius=25,
            command=self.iniciar_investigacion
        )
        self.btn_investigar.pack(pady=(0, 10))
        
        self.btn_exportar = ctk.CTkButton(
            buttons_frame,
            text="💾 Exportar Resultados Completos",
            font=ctk.CTkFont(size=14),
            fg_color=self.colors['success'],
            hover_color="#045D4A",
            text_color="white",
            height=40,
            corner_radius=20,
            command=self.exportar_resultados,
            state="disabled"
        )
        self.btn_exportar.pack()
        
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
        """Iniciar investigación con ambos agentes"""
        if self.is_placeholder:
            messagebox.showwarning("⚠️ Advertencia", "Por favor ingrese las entidades que desea investigar")
            return
            
        entidades_input = self.text_entidades.get("1.0", "end").strip()
        if not entidades_input:
            messagebox.showwarning("⚠️ Advertencia", "Por favor ingrese al menos una entidad")
            return
            
        entidades = [ent.strip() for ent in entidades_input.split('\n') if ent.strip()]
        
        self.btn_investigar.configure(state="disabled", text="🔎 Investigando...")
        self.progress.set(0)
        self.resultados = []
        
        def investigar_thread():
            try:
                self.log_message("🚀 Iniciando sistema de investigación dual", "info")
                self.log_message("🤖 Agente 1: Plataforma Transparencia (Excel Directorio)", "info")
                self.log_message("🌐 Agente 2: Búsqueda Web Contactos", "info")
                self.update_status("🔍 Investigación en progreso...")
                
                total_entidades = len(entidades)
                
                for i, entidad in enumerate(entidades):
                    self.log_message(f"\n🎯 === Investigando: {entidad} ===", "info")
                    
                    # Investigar con ambos agentes en paralelo
                    resultado = self.coordinador.investigar_entidad(entidad, self.log_message)
                    self.resultados.append(resultado)
                    
                    # Actualizar progreso
                    progreso = (i + 1) / total_entidades
                    self.progress.set(progreso)
                    
                    # Resumen de esta entidad
                    excel_ok = resultado['transparencia']['exito']
                    web_ok = resultado['contactos']['exito']
                    
                    self.log_message(f"📊 Resumen {entidad}:", "info")
                    self.log_message(f"   📥 Excel Directorio: {'✅' if excel_ok else '❌'}", "success" if excel_ok else "error")
                    self.log_message(f"   🌐 Contactos Web: {'✅' if web_ok else '❌'}", "success" if web_ok else "error")
                
                # Resumen final completo
                self.log_message(f"\n🎉 ¡Investigación completada!", "success")
                
                excel_exitosos = sum(1 for r in self.resultados if r['transparencia']['exito'])
                web_exitosos = sum(1 for r in self.resultados if r['contactos']['exito'])
                archivos_excel = sum(1 for r in self.resultados if r['transparencia'].get('archivo_descargado'))
                
                self.log_message(f"📈 ESTADÍSTICAS FINALES:", "info")
                self.log_message(f"   • Total entidades: {total_entidades}", "info")
                self.log_message(f"   • Excel directorios descargados: {archivos_excel}/{total_entidades}", "success")
                self.log_message(f"   • Páginas web analizadas: {web_exitosos}/{total_entidades}", "success")
                self.log_message(f"   • Archivos en carpeta: downloads/", "info")
                
                self.update_status("✅ Investigación completada - Datos listos")
                self.btn_exportar.configure(state="normal")
                
                messagebox.showinfo("🎉 Completado", 
                                  f"¡Investigación completada!\n\n"
                                  f"📊 Resultados:\n"
                                  f"• Entidades: {total_entidades}\n"
                                  f"• Excel descargados: {archivos_excel}\n"
                                  f"• Web analizadas: {web_exitosos}\n\n"
                                  f"📁 Archivos en: downloads/")
                
            except Exception as e:
                self.log_message(f"💥 Error crítico del sistema: {str(e)}", "error")
                self.update_status("❌ Error crítico en la investigación")
                messagebox.showerror("Error", f"Error durante la investigación:\n{str(e)}")
            finally:
                self.btn_investigar.configure(state="normal", text="🚀 Iniciar Investigación Dual")
                
        threading.Thread(target=investigar_thread, daemon=True).start()
    
    def exportar_resultados(self):
        """Exportar resultados consolidados"""
        if not self.resultados:
            messagebox.showwarning("Advertencia", "No hay resultados para exportar")
            return
            
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Guardar resumen de investigación"
            )
            
            if filename:
                self.coordinador.exportar_resultados(self.resultados, filename)
                self.log_message(f"💾 Resumen exportado: {filename}", "success")
                messagebox.showinfo("Exportado", f"Resumen guardado en:\n{filename}\n\nLos Excel individuales están en: downloads/")
                
        except Exception as e:
            self.log_message(f"Error exportando: {str(e)}", "error")
            messagebox.showerror("Error", f"Error al exportar:\n{str(e)}")
    
    def run(self):
        """Ejecutar la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TransparenciaContactosApp()
    app.run()