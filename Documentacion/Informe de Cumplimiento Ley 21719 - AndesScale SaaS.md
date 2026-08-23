### Análisis de Impacto y Plan de Adecuación: Ley N° 21.719 en la Plataforma AndesScale

**Documentación técnica y estratégica para la transición al nuevo estándar de protección de datos en Chile**

#### 1\. Introducción y Marco Temporal Estratégico

AndesScale se enfrenta a una transformación profunda en el ecosistema digital chileno. La  **Ley N° 21.719** , publicada el 13 de diciembre de 2024, no es una mera actualización administrativa; es un cambio de paradigma que eleva el estándar de protección de datos personales al nivel del GDPR europeo. Para una plataforma SaaS que sirve como infraestructura para múltiples pymes, la preparación temprana no es solo una obligación de cumplimiento, sino una ventaja competitiva crítica que permitirá a nuestros clientes delegar su confianza en un sistema legalmente resiliente.

##### Contexto Legal y Vigencia

La ley tiene por objeto regular el tratamiento de datos de personas naturales (Art. 1°), estableciendo una  **vigencia diferida hasta el 1 de diciembre de 2026** . Este "periodo de gracia" debe ser utilizado para una refactorización estructural de nuestra arquitectura. La inacción hasta la fecha límite representa un riesgo sistémico, mientras que la adecuación proactiva nos posiciona como el proveedor de CMS y e-commerce más seguro del mercado nacional.

##### Capa de Valor: De-risking como Servicio

Al implementar estas medidas antes de diciembre de 2026, AndesScale actúa como una póliza de seguro para sus clientes. Estamos protegiendo el patrimonio de las pymes frente a multas que pueden alcanzar los 20.000 UTM, transformando el cumplimiento en un habilitador de negocios que reduce la fricción en la venta consultiva.

#### 2\. Definición del Doble Rol Operativo y Riesgos de Responsabilidad

Bajo la Ley N° 21.719, la delimitación de roles no es solo teórica; define quién asume el impacto financiero ante una brecha.

##### AndesScale como Responsable (Art. 2 lit. n)

La plataforma actúa como  **Responsable**  respecto a los datos propios de gestión de cuentas en andesscale.com, invitaciones de equipo y el modelo UserProfile. Aquí, AndesScale decide "fines y medios" y asume la responsabilidad directa ante la Agencia de Protección de Datos Personales.

##### AndesScale como Encargado o Tercero Mandatario (Art. 2 lit. x)

Respecto a los datos procesados por los tenants (ej. los clientes finales de servelec-ingenieria.cl), AndesScale actúa como  **Encargado** . Según el  **Art. 15 bis** , debemos ser extremadamente cautelosos: AndesScale incurrirá en  **responsabilidad solidaria**  con el cliente (el Responsable) si trata los datos fuera de las instrucciones del mandato o si los comunica sin autorización expresa.

##### El Acuerdo de Tratamiento de Datos (DPA) Estandarizado

Para mitigar la responsabilidad solidaria, es imperativo integrar un DPA en los términos de servicio que especifique:

* **Objeto y Duración:**  El servicio técnico de procesamiento.  
* **Finalidad:**  Limitada exclusivamente a la operatividad del e-commerce del tenant.  
* **Categorías de Titulares:**  Clientes finales y leads de los tenants.  
* **Protocolo de Devolución/Eliminación:**  Procedimientos de purga de datos al finalizar el contrato.

#### 3\. Impacto Directo y Requerimientos Técnicos por Módulo

Esta sección traduce los artículos de la ley en requerimientos de código y configuración para nuestro stack  **Django/Neon/Cloudinary** .

##### Módulo apps/website/ (Gestión de Landings y Formularios)

* **Consentimiento Inequívoco (Art. 12):**  Los modelos ContactSubmission no pueden alimentarse de checkboxes pre-marcados. El backend debe registrar el  *timestamp*  y la versión de la política aceptada como prueba de licitud.  
* **Proporcionalidad y Recolección Mínima (Art. 3 lit. c y Art. 14 quáter):**  En el nivel de base de datos en Neon, se deben implementar vistas o el uso de QuerySet.defer() para evitar que procesos secundarios accedan a campos PII (Personally Identifiable Information) que no son estrictamente necesarios para la tarea actual.

##### Módulo apps/accounts/ (Derechos ARCO y Gestión de Plazos)

* **Derecho de Bloqueo (Art. 8 ter y Art. 11):**  Requerimiento técnico de alta prioridad. Se debe añadir un campo is\_blocked\_at (datetime) y un flag status\_blocked al modelo de usuario. Ante una solicitud de rectificación o supresión, el sistema debe disparar un  **trigger automático**  que bloquee el tratamiento (manteniendo solo el almacenamiento) en un plazo máximo de  **2 días hábiles** .  
* **Automatización de Derechos (Art. 4-9):**  El dashboard debe incluir una interfaz para que el usuario descargue sus datos o solicite la supresión. El sistema debe asegurar respuestas legales en un máximo de  **30 días corridos** .

##### Módulo apps/orders/ (Pagos y Transferencia Internacional)

* **Licitud en Flujos Financieros (Art. 13):**  Se justifica el tratamiento de datos de MercadoPago bajo la ejecución del contrato de suscripción, eliminando la necesidad de consentimientos redundantes en el checkout.  
* **Transferencia Internacional (Art. 27 y 28):**  Dado que Neon, Render y Cloudinary procesan datos fuera de Chile, y ante la ausencia de un listado oficial de "países adecuados" por parte de la Agencia, AndesScale debe  **implementar proactivamente Cláusulas Contractuales Tipo (Model Clauses)**  en sus acuerdos de sub-procesamiento de forma inmediata.

##### Módulo apps/marketing/ (Perfilamiento y Art. 8 bis)

* **Decisiones Automatizadas:**  Todo sistema de recomendación o segmentación basado en el comportamiento del usuario debe cumplir con el  **Art. 8 bis** . Esto implica otorgar al titular el derecho a una  **explicación humana**  sobre la lógica aplicada en su perfilamiento y la opción de oponerse a dichas decisiones automatizadas.  
* **Políticas Dinámicas (Art. 14 ter):**  Implementar un motor de plantillas que genere automáticamente la política de privacidad de cada tenant según los módulos que tenga activos (ej. si usa geolocalización, la política debe reflejar el Art. 16 sexies).

#### 4\. Privacidad por Diseño y Seguridad de Infraestructura

La seguridad bajo la Ley N° 21.719 deja de ser una "buena práctica" para convertirse en un mandato legal (Art. 14 quinquies).| Mandato Legal (Art. 14 quinquies) | Implementación Técnica en AndesScale || \------ | \------ || **Seudonimización y Cifrado** | Aplicar cifrado AES-256 en reposo vía Neon para campos sensibles. Seudonimización de IDs en logs. || **Resiliencia y Disponibilidad** | Implementación de Point-in-Time Recovery (PITR) en Neon y redundancia multi-región en Render. || **Integridad y Acceso** | Control de acceso basado en roles (RBAC) estricto en el admin de Django y auditoría de accesos. |

##### Protocolo de Notificación de Brechas (Art. 14 sexies)

En caso de incidente, la notificación a la Agencia debe ser "sin dilaciones indebidas". Si la brecha afecta datos financieros o sensibles, la notificación a los titulares es obligatoria y debe ser redactada en lenguaje claro, especificando las medidas de mitigación adoptadas.

#### 5\. Alineación con el Kanban y Roadmap de Desarrollo

El cumplimiento debe integrarse en el flujo de trabajo actual para optimizar el presupuesto y evitar el re-trabajo futuro.

##### Refactorización de Cards Existentes

* **Card \#54 ("Exportar reportes PDF/CSV"):**  Evoluciona a  **Cumplimiento del Art. 9** . Se debe añadir la opción de exportación en  **formato JSON** , asegurando que sea un formato electrónico estructurado, genérico y de uso común para facilitar la portabilidad directa de responsable a responsable.

##### Nuevas Cards de Prioridad Legal

* **Card \#55:**  Implementación de Lógica de Consentimiento en ContactSubmission (Prohibición de pre-check).  
* **Card \#56:**  Flujo automatizado de Bloqueo Temporal (Art. 8 ter) con resolución en 48 horas.  
* **Card \#57:**  Implementación de lógica de borrado lógico ( *SoftDelete* ) para cumplir con el derecho de supresión manteniendo la integridad referencial para fines de defensa legal (Art. 7 lit. vi).

#### 6\. Matriz de Riesgos, Sanciones y Modelo de Prevención

La Ley N° 21.719 establece un régimen sancionatorio severo administrado por la nueva Agencia.

##### Cuadro de Sanciones (Art. 34 bis \- 35\)

Gravedad de la Infracción,Multa en UTM,Recidencia (% Ingresos Anuales)  
Leve,Hasta 5.000 UTM,N/A  
Grave,Hasta 10.000 UTM,Hasta el 2%  
Gravísima,Hasta 20.000 UTM,Hasta el 4%

##### Modelo de Prevención (Art. 49\)

AndesScale debe evaluar la designación formal de un  **Delegado de Protección de Datos (DPO)**  y la certificación de un  **Modelo de Prevención de Infracciones** . Bajo el  **Art. 36** , contar con un programa de cumplimiento certificado actúa como un  **atenuante legal fundamental**  ante cualquier proceso sancionatorio, protegiendo la valoración de la empresa y su continuidad operacional.**Conclusión:**  La transición técnica debe comenzar de inmediato. Para diciembre de 2026, AndesScale no solo debe estar "al día", sino que debe consolidarse como la infraestructura de confianza que blinda a las pymes chilenas ante los riesgos de la nueva era de la privacidad.  
