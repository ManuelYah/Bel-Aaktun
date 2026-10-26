export interface Artesania {
  id: number;
  taller_id?: number;
  artesano_id?: number;
  nombre_taller: string;       // Nombre del Taller / Cueva
  nombre_pieza: string;       // <--- Agrega esta línea para el nombre del producto
  descripcion?: string;
  precio?: number;
  precio_promedio?: number;
  calidad?: string;
  calidad_partidas?: string;
  imagen_url?: string;
  imagenes?: string[];
  fecha_creacion?: string;
}