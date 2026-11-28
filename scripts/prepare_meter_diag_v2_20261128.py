"""固定コネクタの入力到達先とHOST→親の戻り経路を分離する診断候補。"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'docs/7355_R3_Acceptance_20261128_Rev0'
OLD=CASE/'uart_diagnostic/source'
NEW=CASE/'uart_diagnostic_v2/source'
NEW.mkdir(parents=True)
main=(OLD/'main.c').read_text(encoding='utf-8')
def replace(old,new):
    global main
    assert old in main,old
    main=main.replace(old,new)
replace('static uint32_t rx_total, tx_total, emit_total;',
        'static uint32_t rx_total, tx_total, emit_total;\nstatic uint32_t edges[30], last_pins;')
replace('    uint32_t last=0;',r'''
    // 診断中だけ未使用GPIOを入力化。USB-Aは未接続、native USBの専用端子には触れない。
    // GPIO0はUART TX、1はUART RXを維持。USB-A未接続なので12/13も入力観測する。
    for(uint pin=2;pin<30;pin++) {
        if(pin==23 || pin==24 || pin==25) continue;
        gpio_set_function(pin,GPIO_FUNC_SIO);gpio_set_dir(pin,GPIO_IN);gpio_pull_up(pin);
    }
    last_pins=gpio_get_all();
    uint32_t last=0;''')
replace('        uint8_t input[64];size_t count=0;',r'''
        uint32_t pins=gpio_get_all(), changed=pins^last_pins;
        last_pins=pins;
        for(uint pin=0;pin<30;pin++) if(changed&(1u<<pin)) edges[pin]++;
        uint8_t input[64];size_t count=0;''')
replace('        relay_host_poll(&host,now);',r'''
        int native=getchar_timeout_us(0);
        if(native=='T' && output_offset==output_length) {
            // native USBからの明示自己診断。診断専用sessionの管理応答をUARTへ送る。
            // NF55G・測定器指令を作らず、親は待機中にstale frameとして排除する。
            x1_frame_t request={0};
            memset(request.session,0xA5,8);request.request=0x70000001;
            request.kind='I';request.mode=0;request.timeout_ms=1000;
            request.length=(uint16_t)snprintf((char*)request.payload,sizeof(request.payload),
                                            "%s|0000000100000001",chipid);
            uint8_t selftest[X1_FRAME_MAX];
            size_t length=x1_encode(&request,selftest,sizeof(selftest));
            printf("SELFTEST|origin=native_usb;bytes=%u\n",(unsigned)length);
            relay_host_uart(&host,selftest,length,now);
        }
        relay_host_poll(&host,now);''')
replace('                   (unsigned long)emit_total,(unsigned long)host.rejected_frames,gpio_get(1));',r'''
                   (unsigned long)emit_total,(unsigned long)host.rejected_frames,gpio_get(1));
            printf("EDGES|");
            for(uint pin=0;pin<30;pin++) printf("%u:%lu,",pin,(unsigned long)edges[pin]);
            printf("\n");''')
replace('        sleep_ms(1);','        tight_loop_contents();')
main=main.replace('uartdiag-20261128.1','uartdiag-20261128.2')
(NEW/'main.c').open('x',encoding='utf-8').write(main)
(NEW/'CMakeLists.txt').open('x',encoding='utf-8').write((OLD/'CMakeLists.txt').read_text().replace('uartdiag-20261128.1','uartdiag-20261128.2'))
builder=ROOT/'scripts/build_meter_uart_diag_20261128.py'
code=builder.read_text(encoding='utf-8').replace("/uart_diagnostic'","/uart_diagnostic_v2'").replace('uartdiag-20261128.1','uartdiag-20261128.2')
exec(compile(code,str(builder),'exec'),{'__file__':str(builder),'__name__':'__main__'})
