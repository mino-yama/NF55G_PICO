#ifndef _NF55_TBL_H_
#define _NF55_TBL_H_

typedef struct {
    uint8_t cmd[2];
    uint8_t data_length;
} cmd_tbl_t;

extern const cmd_tbl_t CMD_TBL[VAILD_CMD_ID_NUM];
extern const uint8_t ERROR_RESPONSE_TBL[][ERR_RES_NUM];
extern const uint8_t MONTH_END_TBL[13];
extern const set_parameter_t SET_PRAMETER_DEF_TBL;


extern const uint8_t FFFF_TBL[];
extern const uint8_t FFFFFF_TBL[];

#endif /* _NF55_TBL_H_ */
