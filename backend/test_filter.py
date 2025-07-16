import pandas as pd
from ollama_filter import OllamaContactFilter

def test_ollama_filter():
    """Test the Ollama contact filter with sample data"""
    
    print("🧪 Testing Ollama Contact Filter")
    print("=" * 50)
    
    # Create test data with mix of tech and non-tech positions
    test_data = {
        'Denominación del cargo': [
            'Director de Tecnologías de la Información',
            'Coordinador de Sistemas Informáticos',
            'Jardinero',
            'Jefe de Compras y Adquisiciones',
            'Secretaria Ejecutiva',
            'Director de Innovación y Desarrollo',
            'Chofer',
            'Subdirector de Planeación Estratégica',
            'Personal de Limpieza',
            'Coordinador de Administración y Finanzas',
            'Vigilante',
            'Director de Digitalización'
        ],
        'Nombre(s) de la persona servidora pública': [
            'Juan Carlos Rodríguez',
            'María Elena Fernández',
            'Pedro Sánchez',
            'Ana Gabriela López',
            'Luis Miguel Torres',
            'Carmen Rosa Martínez',
            'José Antonio García',
            'Lucia Patricia Morales',
            'Roberto Silva',
            'Diana Laura Herrera',
            'Carlos Alberto Ruiz',
            'Sofia Isabel Vega'
        ],
        'Correo electrónico oficial, en su caso': [
            'jrodriguez@entidad.gob.mx',
            'mfernandez@entidad.gob.mx',
            'psanchez@entidad.gob.mx',
            'alopez@entidad.gob.mx',
            'ltorres@entidad.gob.mx',
            'cmartinez@entidad.gob.mx',
            'jgarcia@entidad.gob.mx',
            'lmorales@entidad.gob.mx',
            'rsilva@entidad.gob.mx',
            'dherrera@entidad.gob.mx',
            'cruiz@entidad.gob.mx',
            'svega@entidad.gob.mx'
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(test_data)
    
    print("📊 Original test data:")
    print(df[['Denominación del cargo', 'Nombre(s) de la persona servidora pública']].to_string(index=False))
    print(f"\nTotal contacts: {len(df)}")
    
    # Initialize filter
    print("\n🤖 Initializing Ollama filter...")
    try:
        filter = OllamaContactFilter()
        
        # Test Ollama connection first
        print("🔗 Testing Ollama connection...")
        is_connected, message = filter.test_ollama_connection()
        
        if not is_connected:
            print(f"❌ Ollama connection failed: {message}")
            print("📝 Make sure to install Ollama:")
            print("   curl -fsSL https://ollama.ai/install.sh | sh")
            print("   ollama pull llama3.2:1b")
            return
        
        print(f"✅ Ollama connected: {message}")
        
        # Apply filtering
        print("\n🔍 Applying filter...")
        filtered_df = filter.filter_contacts_batch(df)
        
        print(f"\n📋 Filtered results:")
        if not filtered_df.empty:
            print(filtered_df[['Denominación del cargo', 'Nombre(s) de la persona servidora pública']].to_string(index=False))
            print(f"\nFiltered contacts: {len(filtered_df)}")
            print(f"Filter efficiency: {len(filtered_df)}/{len(df)} ({len(filtered_df)/len(df)*100:.1f}%)")
            
            print(f"\n✅ Expected tech-related positions to be kept:")
            expected_kept = [
                'Director de Tecnologías de la Información',
                'Coordinador de Sistemas Informáticos', 
                'Jefe de Compras y Adquisiciones',
                'Director de Innovación y Desarrollo',
                'Subdirector de Planeación Estratégica',
                'Coordinador de Administración y Finanzas',
                'Director de Digitalización'
            ]
            
            for pos in expected_kept:
                if pos in filtered_df['Denominación del cargo'].values:
                    print(f"   ✅ {pos}")
                else:
                    print(f"   ❌ {pos} (should have been kept)")
            
        else:
            print("❌ No contacts passed the filter")
            
    except Exception as e:
        print(f"❌ Error testing filter: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ollama_filter()
