# zmote
Zmote custom component for Home Assistant. Zmote code is borrowed from [initialed85's](https://github.com/initialed85/zmote) module. Many thanks.
Currently doesn't support command learning. Use zmote's own interface.

## Installation in Home Assistant:

1. Install this component by copying `custom_components/zmote` to your `config` folder
2. Add platform to your configuration.yaml
3. Restart Home Assistant


## Example configuration:
```
remote:
  - platform: zmote
    host: 192.168.0.10
    devices:
      - name: Yamaha Stereo Receiver
        commands:
          - name: "TOGGLE"
            data: "1:1,0,38000,2,69,343,171,21,22,21,65CCCCCBCBBBBBBCBCBCBCBBCBCBCBCC21,1672,343,86,21,3730"
          - name: "ON"
            data: "1:1,0,38000,2,1,343,171,21,22,21,65CCCCCBCBBBBBBCBCCCCCCBCBBBBBBC21,1672"
          - name: "OFF"
            data: "1:1,0,38000,2,1,343,171,21,22,21,65CCCCCBCBBBBBBCCCCCCCCBBBBBBBBC21,1672"
```

For `remote.turn_on` and `remote.turn_off` functionality you have to have ON and OFF commands declared.