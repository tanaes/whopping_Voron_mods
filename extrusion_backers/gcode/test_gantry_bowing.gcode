BED_MESH_CLEAR                      ; clear bed mesh
G28                                 ; home
QUAD_GANTRY_LEVEL                   ; tram
G28                                 ; home
M140 S105                           ; set bed temp
M190 S105                           ; wait for bed to reach temp
BED_MESH_CALIBRATE                  ; read bed mesh
BED_MESH_PROFILE SAVE=test_cold     ; save bed mesh as 'test_cold'
BED_MESH_OUTPUT
G4 P7200000                         ; wait for 2 hours
BED_MESH_CLEAR                      ; clear bed mesh
BED_MESH_CALIBRATE                  ; read bed mesh
BED_MESH_PROFILE SAVE=test_hot      ; save bed mesh as 'test_hot'
SAVE_CONFIG
BED_MESH_OUTPUT